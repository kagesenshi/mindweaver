# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.fw.permission import (
    Permission,
    Read as FwRead,
    Write as FwWrite,
    List as FwList,
    View as FwView,
    Create as FwCreate,
    Update as FwUpdate,
    Delete as FwDelete,
    Execute as FwExecute,
)


class Manage(Permission):
    """Base permission for all operations on S3 Storage resources."""

    name: str = "s3_storage:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on s3 storage."""

    name: str = "s3_storage:read"


class List(Read, FwList):
    """Permission to list s3 storages."""

    name: str = "s3_storage:list"


class View(Read, FwView):
    """Permission to view a specific s3 storage and its configuration."""

    name: str = "s3_storage:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on s3 storage."""

    name: str = "s3_storage:write"


class Create(Write, FwCreate):
    """Permission to create a new s3 storage connection."""

    name: str = "s3_storage:create"


class Update(Write, FwUpdate):
    """Permission to update an existing s3 storage connection."""

    name: str = "s3_storage:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing s3 storage connection."""

    name: str = "s3_storage:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions and operational tasks on s3 storage."""

    name: str = "s3_storage:execute"


class TestConnection(Execute):
    """Permission to test connection to an S3 storage."""

    name: str = "s3_storage:test_connection"


class FsRead(View):
    """Permission to browse buckets and read objects in S3 storage."""

    name: str = "s3_storage:fs_read"


class FsWrite(Write):
    """Permission to upload and delete objects in S3 storage."""

    name: str = "s3_storage:fs_write"


# Canonical Aliases (S3Storage*)
ManageS3Storage = Manage
ManageS3StoragePermission = Manage
S3Storage = Manage
S3StoragePermission = Manage
S3StorageRead = Read
S3StorageList = List
S3StorageView = View
S3StorageWrite = Write
S3StorageCreate = Create
S3StorageUpdate = Update
S3StorageDelete = Delete
S3StorageExecute = Execute
S3StorageTestConnection = TestConnection
S3StorageFsRead = FsRead
S3StorageFsWrite = FsWrite

# Canonical Aliases (S3*)
ManageS3 = Manage
ManageS3Permission = Manage
S3 = Manage
S3Permission = Manage
S3Read = Read
S3List = List
S3View = View
S3Write = Write
S3Create = Create
S3Update = Update
S3Delete = Delete
S3Execute = Execute
S3TestConnection = TestConnection
S3FsRead = FsRead
S3FsWrite = FsWrite
