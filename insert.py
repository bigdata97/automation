INSERT INTO cc_work_additional_details (
  queue_id, process_type, file_filters, source_type, source_location, source_path,
  target_type, target_location, target_path, file_names, APMID, Application_Name,
  job_name, process_id, dependency_job, reference, schedule_type, status,
  created_by, created_ts, modified_by, modified_ts, scheduler, gcp_tenancy,
  job_group, total_script_files, start_type, branch_name
)
VALUES (
  6666, 'code_discovery', '', 'Composer', 'GitHub Aetna', 'cradl/cradl-dataprocessing-framework',
  'APMO015909', 'ABC CADL GWTH Analytics', 1, 'Code_Discovered', 'Madire',
  TIMESTAMP("2025-07-02T14:09:52.114805Z"), 'system', TIMESTAMP("2025-07-02T14:10:56.128195695Z"),
  'Composer', 'Repo', '', 0, 'master'
);
