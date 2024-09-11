### just for reference for later, remove this later ###
# Step 5: Trigger the S3 upload DAG after scraper finishes
trigger_s3_upload = TriggerDagRunOperator(
    task_id='trigger_upload_to_s3',
    trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
    wait_for_completion=False,               # Do not wait for the upload DAG to complete
    trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
    dag=dag
)
### ###

# =======================
# Set Up Task Dependencies
# =======================

# Based on the check, either proceed with the cleaning -> scraping -> sorting, or end the DAG
check_changes_task >> [clean_bclaws_task, no_changes_task]  
clean_bclaws_task >> scrape_task  # Clean before scraping
scrape_task >> sort_files_task    # Sort files after scraping
sort_files_task >> trigger_html_scraper  # Trigger HTML Scraper after sorting is complete

### just for reference for later, remove this later ###
sort_files_task >> trigger_s3_upload  # Trigger S3 upload only after sorting is complete
### ###
