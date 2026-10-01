# Changelog

## Local changes

### SOMEF integration & use of it
- Updated somef -> 0.11.4
- Added optional `GITHUB_API_TOKEN` support in `saltbot configure` by `saltbot configure` cli && ``configure_from_env.sh`` script
- `describe` now passes the GitHub token to SOMEF using `--github-token` when configured
- Replaced SOMEF `os.system(...)` calls with `subprocess.run([...], check=True)` while preserving SOMEF console logs
- Added clearer SOMEF execution error messages

### Research of articles & software
- Changed WikidataApi queries -> WikidataSPARQLApi queries in the command `saltbot describe` to avoid API rate limits
- Ignored `type: software` citations when looking for scholarly articles
- Prevented software-only operations when no scientific article is found
- Added research of software in wikidata by the repository URL instead of only using the repository name 
- the software research by URL includes the subclasses of software


### Internal Data management
- Now SALTBot generates a diferent operation_list.txt and results.txt for different softwares. with the formats `repoOrg_repoName_operation_list.txt` && `repoOrg_repoName_result.txts` 

### General
- Normalized repository/download URLs before generating URL statements
- Normalized article DOI values and emits DOI as `ExternalID`
- Added `ExternalID` handling in the updater.
- Improved logs when article and software are already linked or when no operations are generated
- Added a wikidata rateLimit (0.5s) between requests to not overwhelm WikidataApi
- Changed SALTBot internal logic: if somef does not detect articles related to the repository, SALTBOT will stop its execution
- Added flag `--fallback-search`: if somef does not detect articles related to the repository, SALTBot searchs in Wikidata if there are articles related to the repository name
- Added batch update support through saltbot update ``--operations-dir operations``. This mode merges all ``operations/*_operations.txt`` files into ``final_operation_list.txt``, overwriting it on each run.
The update is then executed from the merged file, while the existing ``--file`` mode remains available for single-repository updates.
If no operation files are found, SALTBot exits without logging in or writing to Wikidata.
- Fixed minor bugs related to the reading of somef extractions