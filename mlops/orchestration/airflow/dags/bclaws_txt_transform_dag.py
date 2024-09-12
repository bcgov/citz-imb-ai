# # Step 5: Trigger the S3 upload DAG after transformations finish
# trigger_s3_upload = TriggerDagRunOperator(
#     task_id='trigger_upload_to_s3',
#     trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
#     wait_for_completion=False,               # Do not wait for the upload DAG to complete
#     trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
#     dag=dag
# )
# ### ###

# # =======================
# # Set Up Task Dependencies
# # =======================

# trigger_s3_upload


