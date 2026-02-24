# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import fastapi
from fastapi import HTTPException, Depends, File, UploadFile
from typing import Any, Literal, Optional, Annotated
from pydantic import BaseModel
import asyncio
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from mindweaver.config import settings
from mindweaver.crypto import decrypt_password, EncryptionError
from mindweaver.fw.exc import FieldValidationError, MindWeaverError
from .service import S3StorageService, S3Storage


def _list_objects_sync(s3_client, bucket: str, prefix: str):
    """
    Synchronously list objects in S3 bucket using paginator.
    This function is intended to be run in a separate thread.
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    # Use delimiter to get "folders"
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")

    items = []
    for page in pages:
        # Add folders (CommonPrefixes)
        for cp in page.get("CommonPrefixes", []):
            items.append(
                {
                    "name": cp["Prefix"].split("/")[-2] + "/",
                    "path": cp["Prefix"],
                    "type": "directory",
                }
            )

        # Add files (Contents)
        for obj in page.get("Contents", []):
            # Skip the prefix itself if it appears as an object (common in some S3 implementations for folders)
            if obj["Key"] == prefix:
                continue

            items.append(
                {
                    "name": obj["Key"].split("/")[-1],
                    "path": obj["Key"],
                    "type": "file",
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
            )

    return {
        "type": "objects",
        "bucket": bucket,
        "prefix": prefix,
        "items": items,
    }


class VerifyEncryptedRequest(BaseModel):
    secret_key: str


class TestConnectionRequest(BaseModel):
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    verify_ssl: Optional[bool] = None
    storage_id: Optional[int] = None


if settings.enable_test_views:

    @S3StorageService.model_view(
        method="POST",
        path="/_verify-encrypted",
        operation_id=f"mw-verify-encrypted-{S3StorageService.entity_type()}",
    )
    async def verify_encrypted(
        svc: Annotated[S3StorageService, Depends(S3StorageService.get_service)],
        model: Annotated[S3Storage, Depends(S3StorageService.get_model)],
        data: VerifyEncryptedRequest,
    ) -> bool:
        return svc.verify_secret_key(model, data.secret_key)


@S3StorageService.model_view(
    method="GET",
    path="/_fs",
    operation_id=f"mw-fs-{S3StorageService.entity_type()}",
)
async def fs_ops(
    svc: Annotated[S3StorageService, Depends(S3StorageService.get_service)],
    model: Annotated[S3Storage, Depends(S3StorageService.get_model)],
    request: fastapi.Request,
    action: Literal["ls", "get"] = "ls",
    bucket: Optional[str] = None,
    prefix: str = "",
    key: Optional[str] = None,
):
    region = model.region
    access_key = model.access_key
    secret_key = None
    endpoint_url = model.endpoint_url
    verify_ssl = model.verify_ssl

    if model.secret_key:
        try:
            secret_key = decrypt_password(model.secret_key)
        except EncryptionError:
            pass

    try:
        # Create S3 client
        s3_config = {
            "aws_access_key_id": access_key,
            "region_name": region,
        }

        if secret_key:
            s3_config["aws_secret_access_key"] = secret_key

        if endpoint_url:
            s3_config["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", verify=verify_ssl, **s3_config)

        if action == "ls":
            if not bucket:
                # List buckets
                response = await asyncio.to_thread(s3_client.list_buckets)
                return {
                    "type": "buckets",
                    "items": [
                        {
                            "name": b["Name"],
                            "creation_date": b["CreationDate"].isoformat(),
                        }
                        for b in response.get("Buckets", [])
                    ],
                }
            else:
                # List objects in bucket
                return await asyncio.to_thread(
                    _list_objects_sync, s3_client, bucket, prefix
                )

        elif action == "get":
            if not bucket or not key:
                raise HTTPException(
                    status_code=400,
                    detail="Bucket and Key are required for 'get' action",
                )

            # Generate presigned URL for the user to download directly
            try:
                presigned_url = await asyncio.to_thread(
                    s3_client.generate_presigned_url,
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=3600,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate presigned URL: {str(e)}",
                )

            # If the client explicitly requests JSON, return the URL as JSON
            # This is useful for frontend to handle the redirect manually (e.g. window.open)
            accept = request.headers.get("accept", "")
            if "application/json" in accept:
                return {"url": presigned_url}

            # Default to redirecting the browser
            return fastapi.responses.RedirectResponse(presigned_url, status_code=307)

        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise HTTPException(
            status_code=400, detail=f"S3 Error ({error_code}): {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@S3StorageService.model_view(
    method="POST",
    path="/_fs",
    operation_id=f"mw-fs-post-{S3StorageService.entity_type()}",
)
async def fs_ops_post(
    svc: Annotated[S3StorageService, Depends(S3StorageService.get_service)],
    model: Annotated[S3Storage, Depends(S3StorageService.get_model)],
    bucket: str,
    action: Literal["put", "rm"] = "put",
    prefix: str = "",
    key: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
) -> dict[str, Any]:
    region = model.region
    access_key = model.access_key
    secret_key = None
    endpoint_url = model.endpoint_url
    verify_ssl = model.verify_ssl

    if model.secret_key:
        try:
            secret_key = decrypt_password(model.secret_key)
        except EncryptionError:
            pass

    try:
        # Create S3 client
        s3_config = {
            "aws_access_key_id": access_key,
            "region_name": region,
        }

        if secret_key:
            s3_config["aws_secret_access_key"] = secret_key

        if endpoint_url:
            s3_config["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", verify=verify_ssl, **s3_config)

        if action == "put":
            if not file:
                raise HTTPException(
                    status_code=400, detail="File is required for 'put' action"
                )

            # Ensure prefix ends with / if specified and not already there
            if prefix and not prefix.endswith("/"):
                prefix += "/"

            key = f"{prefix}{file.filename}"

            # Upload to S3
            await asyncio.to_thread(s3_client.upload_fileobj, file.file, bucket, key)

            return {
                "status": "success",
                "message": f"Successfully uploaded '{file.filename}' to '{bucket}/{prefix}'",
                "bucket": bucket,
                "key": key,
            }

        if action == "rm":
            if not key:
                raise HTTPException(
                    status_code=400, detail="Key is required for 'rm' action"
                )

            # Delete from S3
            await asyncio.to_thread(s3_client.delete_object, Bucket=bucket, Key=key)

            return {
                "status": "success",
                "message": f"Successfully deleted '{key}' from '{bucket}'",
                "bucket": bucket,
                "key": key,
            }

        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise HTTPException(
            status_code=400, detail=f"S3 Error ({error_code}): {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status=500, detail=str(e))


@S3StorageService.service_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection(
    data: TestConnectionRequest,
    svc: S3StorageService = Depends(S3StorageService.get_service),
):
    """
    Test connection to S3 storage.
    If storage_id is provided and secret_key is missing, use stored secret.
    """
    # Initialize variables from request
    region = data.region
    access_key = data.access_key
    secret_key = data.secret_key
    endpoint_url = data.endpoint_url
    verify_ssl = data.verify_ssl

    # If storage_id is provided, check for stored secret_key if missing in request or redacted
    if data.storage_id:
        existing = await svc.get(data.storage_id)
        if (
            existing
            and existing.secret_key
            and (not secret_key or secret_key == "__REDACTED__")
        ):
            try:
                secret_key = decrypt_password(existing.secret_key)
            except EncryptionError:
                pass

        if verify_ssl is None:
            verify_ssl = existing.verify_ssl

    try:
        if not region:
            raise ValueError("Region is required")
        if not access_key:
            raise ValueError("Access key is required")

        if verify_ssl is None:
            verify_ssl = True

        # Try to connect to S3 using boto3
        try:
            # Create S3 client
            s3_config = {
                "aws_access_key_id": access_key,
                "region_name": region,
            }

            if secret_key:
                s3_config["aws_secret_access_key"] = secret_key

            if endpoint_url:
                s3_config["endpoint_url"] = endpoint_url

            s3_client = boto3.client("s3", verify=verify_ssl, **s3_config)

            # Try to list buckets to verify access
            await asyncio.to_thread(s3_client.list_buckets)

            return {
                "status": "success",
                "message": f"Successfully connected to S3 in region '{region}'",
            }

        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "403":
                raise ValueError(f"Access denied: {str(e)}")
            else:
                raise ValueError(f"S3 connection failed: {str(e)}")

    except MindWeaverError:
        raise
    except Exception as e:
        raise FieldValidationError(message=str(e))
