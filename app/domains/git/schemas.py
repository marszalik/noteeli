from __future__ import annotations

from pydantic import BaseModel, Field


class GitFileChange(BaseModel):
    path: str
    # One of: modified | added | deleted | untracked | renamed | conflict
    status: str
    staged: bool = False


class GitStatus(BaseModel):
    available: bool = False        # storage backend can host git at all (local/sftp)
    is_repo: bool = False
    branch: str = ""
    upstream: str = ""
    ahead: int = 0
    behind: int = 0
    clean: bool = True
    files: list[GitFileChange] = Field(default_factory=list)


class GitCommitRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # When given, only these paths are staged (relative to the workspace
    # root). Empty / omitted → stage everything (git add -A).
    paths: list[str] = Field(default_factory=list)
    push: bool = False             # commit then push in one call


class GitOpResult(BaseModel):
    ok: bool
    message: str = ""
    output: str = ""
