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


## Dedicated private scanner service

The standalone `backend/private_scanner/Dockerfile` is an optional independently deployed scanner. Use an authorized US host with sufficient memory for official ClamAV signatures, scanning and updates (budget at least 2–4 GiB and measure real peaks; the current Render free instance is not adequate). Build using `docker build -t krafzen-private-scanner backend/private_scanner`. Run with a strong random PRIVATE_SCANNER_TOKEN supplied via a secret store and a private, persistent /var/lib/clamav signature volume writable by the clamav user. Terminate TLS at a trusted HTTPS reverse proxy, restrict inbound access to the authorized backend, disable request-body logging, set max body 40 MiB and appropriate timeouts. Do not expose the unencrypted container port publicly. Deploy only after the operator verifies the host, processing region, backups/logs and contractual data handling.

The backend supports PRIVATE_SCANNER_URL (HTTPS origin), PRIVATE_SCANNER_TOKEN (same secret) and PRIVATE_SCANNER_US_PROCESSING_APPROVED=true (set only after independent approval). By default no uploads are sent to another host. Authentication and TLS are mandatory. A response must bind to the submitted SHA-256 and byte count, contain current official signature metadata, and return a clean/rejected verdict. A missing, stale or invalid response fails closed. The remote health check executes actual benign and EICAR scans; it can consume a scanner slot and should be used sparingly. Do not enable this for sovereign-tenant projects until the full regional pipeline is approved. No customer files are retained by this service; temporary files are deleted after processing.

This is deployable code, not proof that a separately approved host exists or has been activated. No paid host is provisioned automatically.
