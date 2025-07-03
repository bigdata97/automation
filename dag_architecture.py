I wanted to inform you about a limitation I’ve encountered in the DAG parsing script I developed for analyzing Git repos.

The current approach successfully parses standard DAGs, extracts their dependent files, and identifies table names referenced in those files. However, I’ve observed that some of the Retail-specific DAGs follow a different design pattern. These DAGs rely on a generic wrapper method, where task configuration is passed as arguments. The actual job details are then retrieved dynamically from a SQL table at runtime.

Since the job logic is not explicitly defined in code but fetched externally, our current parsing logic cannot resolve the job/task-level details from these DAGs.

Please let me know if you’d like me to explore potential ways to enhance the parser to handle this pattern or if we should document this as a known limitation.
