
**Brief Overview:**

1. Install DVC with S3 support:

   ```bash
   pip install "dvc[s3]"
   ```

2. Set environment variables:

   ```bash
   export AWS_ACCESS_KEY_ID=<your-access-key>
   export AWS_SECRET_ACCESS_KEY=<your-secret-key>
   export AWS_DEFAULT_REGION=ca-central-1
   export AWS_REQUEST_CHECKSUM_CALCULATION='WHEN_REQUIRED'
   ```

3. Pull data from S3 (approx. 10GB+; this can take some time):

   ```bash
   dvc pull
   ```

4. All data will be stored in the `data` folder.

To push updates to S3, use DVC similarly to Git:

- Add your data folder:

  ```bash
  dvc add data/<your-folder>
  ```

- Commit changes (updates the hash):

  ```bash
  git commit -m "Update data hash"
  ```

- Push your data to s3:

  ```bash
  dvc push
  ```

- Push changes to Git (open a PR with the new hash). This step is critical—if the hash is corrupted, data retrieval becomes problematic:

  ```bash
  git push
  ```

Always ensure your DVC and Git operations are synchronized to maintain data integrity.