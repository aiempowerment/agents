class FilesS3Service:

    def __init__(self, tenant_config, s3_client):
        s3_config = tenant_config.get("s3", {})
        self.bucket = s3_config.get("bucket")
        self.s3 = s3_client

        if not self.bucket:
            raise ValueError("S3_BUCKET_MISSING")

    def list_files(self, directory: str, extensions=None) -> list[str]:
        if not directory:
            raise ValueError("DIRECTORY_MISSING")

        if not directory.endswith("/"):
            raise ValueError("DIRECTORY_MUST_END_WITH_SLASH")

        normalized_exts = None
        if extensions:
            normalized_exts = {
                e.lower().lstrip(".")
                for e in extensions
                if isinstance(e, str) and e.strip()
            }

        files: list[str] = []
        token = None

        while True:
            kwargs = {
                "Bucket": self.bucket,
                "Prefix": directory,
                "MaxKeys": 1000,
            }

            if token:
                kwargs["ContinuationToken"] = token

            resp = self.s3.list_objects_v2(**kwargs)

            for obj in resp.get("Contents", []) or []:
                key = obj["Key"]

                if key.endswith("/"):
                    continue

                if normalized_exts:
                    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                    if ext not in normalized_exts:
                        continue

                files.append(key)

            if not resp.get("IsTruncated"):
                break

            token = resp.get("NextContinuationToken")

        return files