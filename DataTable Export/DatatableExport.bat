@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
:: This script exports post call survey results, and begins the process for process automation
:: Define the datatable ID
SET datatableId=ab8ec66e-ce0e-490d-8e66-2cfa4a99faa0

:: Define your clientId and clientSecret
SET clientId=b0ef4527-e7c7-4885-be0b-8382e6b4c3a2
SET clientSecret=cpA6qWCJrTFmmJ7WN9sZEWK_ZDCfGAWscGu2s95pKJo

:: Run the create export job command and capture the job ID
gc flows datatables export jobs create %datatableId% --outputformat json > export_job_create_output.json
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to create export job.
    type export_job_create_output.json
    exit /b
)

:: Display the result for debugging purposes
echo Result of export job creation:
type export_job_create_output.json

:: Use jq to parse the job ID from the JSON output (make sure jq is in your PATH)
FOR /F "delims=" %%a IN ('jq -r ".id" export_job_create_output.json 2^>^&1') DO SET jobId=%%a

:: Check if we got a jobId
IF NOT DEFINED jobId (
    echo Error: Job ID not found.
    exit /b
)

echo Job ID: !jobId!

:: Check the status of the export job
:checkStatus
gc flows datatables export jobs get %datatableId% !jobId! --outputformat json > export_job_status_output.json
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to check export job status.
    type export_job_status_output.json
    exit /b
)

:: Use jq to parse the status and download URI from the JSON output
FOR /F "delims=" %%a IN ('jq -r ".status" export_job_status_output.json') DO SET status=%%a
FOR /F "delims=" %%b IN ('jq -r ".downloadURI" export_job_status_output.json') DO SET downloadURI=%%b

:: Check if the status is "Succeeded"
IF "!status!" NEQ "Succeeded" (
    echo Job status: !status!. Waiting for completion...
    TIMEOUT /T 10
    goto checkStatus
)

echo Job completed with status: !status!

:: Validate if we got a downloadURI
IF NOT DEFINED downloadURI (
    echo Error: Download URI not found.
    exit /b
)

:: Create PowerShell script content
SET PS_Script=^
$clientId='%clientId%';^
$clientSecret='%clientSecret%';^
$body=@{'grant_type'='client_credentials';'client_id'=$clientId;'client_secret'=$clientSecret};^
$response=Invoke-RestMethod -Method Post -Uri 'https://login.mypurecloud.com.au/oauth/token' -Body $body;^
$token=$response.access_token;^
$headers=@{'Authorization'='Bearer '+$token};^
Invoke-WebRequest -Uri '%downloadURI%' -Headers $headers -OutFile 'exported_data.csv';^
Write-Host 'Download complete!'

:: Encode the PowerShell script to base64
SET EncodedScript=powershell -Command "[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Env:PS_Script))"

:: Execute the base64 encoded PowerShell script
FOR /F "delims=" %%i IN ('!EncodedScript!') DO SET B64=%%i
PowerShell -EncodedCommand !B64!

IF %ERRORLEVEL% NEQ 0 (
    echo Failed to download the file.
    exit /b
)

echo Download complete!

:: Send an email with the CSV file as an attachment using PowerShell
powershell -ExecutionPolicy Bypass -Command "Send-MailMessage -To 'addyouremail' -From 'addyouremail' -Subject 'PostCallSurveyAutomate' -Body 'Please find the attached CSV file. sigrem' -SmtpServer 'add your SMTP' -Attachments 'exported_data.csv'"

ENDLOCAL