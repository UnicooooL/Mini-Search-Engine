Live Server Address:
Public IP - 34.202.237.118:8080
Access Method - Port forwarding to local host(see below)
Pem File Name - ece326-key-1.pem

Testing Method	
Port forwarding via ssh to (localhost:8080)
Command to go to localhost: ssh -i ece326-key-1.pem -L 8080:localhost:8080 ubuntu@34.202.237.118
And then go to http://localhost:8080/ on any browser


Benchmark Setup	- Instance type used (t3.micro), concurrency tested, and monitoring tools used (ab, dstat)
Benchmarking command - 
ab -n 500 -c 5 http://172.31.31.66:8080/

Deliverables Summary:
Frontened Source Code (app.py) in lab2_frontened folder 
Backened Source Code in lab2 folder (launch_ec2.py) - AWS key replaced with 'xxxxxxxxxx'
RESULT file also included, it contains all benchmark measurements.
Security File: ece326-key-1.pem included for port forwarding