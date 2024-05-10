# UCMA | GitLab Git Processor Plugin

Git processor plugin, which can be used to analyze remote Git repository, hosted on [GitLab.com](https://gitlab.com) or its self-hosted version.

**Install**

``` bash
poetry add git+https://github.com/Universal-code-metrics-analyzer/gitlab-git-processor@v0.1.0
```

**Runner configuration**

``` yaml
# config.yml

git_processor:
  plugin: gitlab_git_processor
  config:
    # host of GitLab instance
    api_host: https://gitlab.com
    # id of the project to analyze
    project_id: 11112222
    # [optional] api token used to authorize api calls in case a project is private
    api_token: my-secret-token
```
