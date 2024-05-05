import os
import shutil
import tarfile
from pathlib import Path
from typing import Any

import aiofiles
from aiohttp import ClientSession
from core.git_processor import (
    BlobData,
    GitProcessor,
    GitProcessorConfigShape,
    TreeData,
)
from pydantic import AnyHttpUrl


class GitLabGitProcessorConfigShape(GitProcessorConfigShape):
    api_host: AnyHttpUrl
    project_id: int
    api_token: str | None = None


class GitLabGitProcessor(
    GitProcessor[GitLabGitProcessorConfigShape, Path, Path],
    config_shape=GitLabGitProcessorConfigShape,
):
    def __init__(self, config_dict: dict[str, Any], ref: str) -> None:
        super().__init__(config_dict, ref)
        self.tar_path = Path(f'./{ref}.tar.gz')
        self.temp_path = Path(f'./{ref}')

    def strip_temp(self, path: Path) -> str:
        return str(path).removeprefix(str(self.temp_path)).removeprefix('/')

    async def get_root_tree(self) -> Path:
        headers: dict[str, str] = {}
        if self.config.api_token:
            headers['Authorization'] = f'Bearer {self.config.api_token}'

        async with ClientSession(str(self.config.api_host), headers=headers) as session:
            async with session.get(
                f'/api/v4/projects/{self.config.project_id}'
                + f'/repository/archive.tar.gz?sha={self.ref}'
            ) as request:
                async with aiofiles.open(self.tar_path, 'wb') as f:
                    await f.write(await request.read())

                with tarfile.open(self.tar_path, mode='r:gz') as tar:
                    members = tar.getmembers()
                    root = members[0].path

                    for el in tar.getmembers():
                        el.name = el.name.replace(root, str(self.temp_path))
                        tar.extract(el, filter='data')

        return self.temp_path

    async def process_blob(self, blob: Path, depth: int) -> BlobData:
        blob_path = self.strip_temp(blob)

        with open(blob, 'r') as file:
            return BlobData(
                name=blob.name,
                path=blob_path,
                content=file.read(),
            )

    async def process_tree(self, tree: Path, depth: int) -> TreeData:
        tree_path = self.strip_temp(tree)

        blob_datas: list[BlobData] = []
        tree_datas: list[TreeData] = []

        for el in tree.iterdir():
            if el.is_dir():
                tree_datas.append(await self.process_tree(Path(el), depth + 1))
            else:
                blob_datas.append(await self.process_blob(Path(el), depth))

        return TreeData(
            name=tree.name,
            path=tree_path,
            trees=tree_datas,
            blobs=blob_datas,
        )

    async def cleanup(self) -> None:
        shutil.rmtree(self.temp_path)
        os.remove(self.tar_path)
