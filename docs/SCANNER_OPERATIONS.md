# Scanner deployment and acceptance contract

The native free Render service is NOT suitable for the full official ClamAV database (512 MB RAM). No change to paid compute is authorized. The Docker image now installs ClamAV and FreshClam. A separately authorized adequately sized, region-approved host must refresh the signature database with FreshClam and maintain scheduled updates; do not install substitute signatures or disable scanner gates. The operator must ensure an accessible /var/lib/clamav directory and current official signature databases before enabling uploads.

Every upload uses official signatures only, rejects signatures older than three days, blocks encrypted or over-limit content, and allows only one ClamAV process per API worker. Deploy one worker on a constrained scanner host; budget RAM for the application, parser and scanner. Public health checks only inspect signature date metadata (bounded cached version command); they do not claim to have verified malware detection or storage.

Release tests: run the isolated CI scanner import tests; on the hosted scanner run a benign file scan and an official EICAR test file scan locally; verify the latter is rejected and a real DXF/IFC import succeeds; verify stale signatures, missing scanner and concurrency reject safely. Keep customer documents private and in their approved region. Do not transmit them to a public scanning website.

References:
- https://docs.clamav.net/
- https://docs.clamav.net/manual/Usage/SignatureManagement.html
- https://docs.clamav.net/manual/Usage/Scanning.html
- https://render.com/docs/compute-plans

This code does not provision a scanner host, refresh live signatures, or claim a production scan passed.
