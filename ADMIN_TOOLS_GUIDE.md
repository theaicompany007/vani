# Admin Tools Guide

## Overview

The Admin Tools system provides super administrators with powerful batch processing capabilities for managing large-scale contact imports and system operations. This is especially useful for importing 1000+ contacts efficiently.

## Access

Admin Tools are only accessible to **super users**. To access:

1. Log in as a super user
2. Click the **"Admin Tools"** tab in the navigation bar
3. You'll see:
   - System Information
   - Batch Contact Import interface

## Features

### 1. System Information

View real-time system metrics:
- Platform and Python version
- CPU cores
- Memory usage (total, available, used percentage)
- Disk usage (total, used, free, percentage)

### 2. Batch Contact Import

Import contacts from Excel files with advanced batch processing:

#### Features:
- **Batch Processing**: Process contacts in batches (100-500 records per batch) to manage memory efficiently
- **Multi-Threading**: Use 1-16 parallel threads for faster processing
- **All Sheets Support**: Process all sheets or specify a single sheet
- **Update Existing**: Option to update existing contacts
- **Import Only New**: Skip duplicates and only import new contacts
- **Dry Run**: Preview mode to test without actually importing

#### Usage:

1. **Enter Excel File Path**
   - Relative to project root (e.g., `data/the_ai_company.xlsx`)
   - File must exist in the `data/` directory or provide full path

2. **Configure Settings**
   - **Batch Size**: Number of records per batch (default: 100, range: 10-500)
   - **Threads**: Number of parallel threads (default: 4, range: 1-16)
   - **Sheet Name**: Leave empty for all sheets, or specify a sheet name

3. **Select Options**
   - ☑ **Update existing contacts**: Update contacts that already exist
   - ☑ **Import only new**: Skip duplicates, only import new contacts
   - ☑ **Dry run**: Preview only, don't actually import

4. **Run Import**
   - Click "Run Batch Import"
   - Check the status display for process ID and command
   - Monitor logs in `logs/batch_import_*.log`

#### Example:

```
Excel File: data/the_ai_company.xlsx
Batch Size: 100
Threads: 4
Sheet Name: (empty - process all sheets)
Options: ☑ Import only new
```

## Command Line Usage

You can also run the batch import script directly from the command line:

### Basic Usage

```bash
python scripts/import_contacts_batch.py data/the_ai_company.xlsx
```

### Advanced Options

```bash
python scripts/import_contacts_batch.py data/the_ai_company.xlsx \
    --batch-size 200 \
    --threads 8 \
    --update-existing \
    --sheet education_leads \
    --dry-run
```

### Options:

- `--batch-size`: Number of records per batch (default: 100)
- `--threads`: Number of parallel threads (default: 4)
- `--update-existing`: Update existing contacts
- `--import-only-new`: Only import new contacts, skip duplicates
- `--sheet`: Specific sheet name to import (default: all sheets)
- `--dry-run`: Preview mode, don't actually import

### Example Output:

```
================================================================================
Starting batch contact import
File: data/the_ai_company.xlsx
Batch size: 100
Threads: 4
Update existing: False
Import only new: False
Dry run: False
================================================================================
Loading Excel file: data/the_ai_company.xlsx
Excel file contains 2 sheet(s): education_leads, cxo_leads
Processing all sheets: education_leads, cxo_leads
Processing sheet: education_leads
Sheet 'education_leads': Processed 1500 rows, extracted 1480 contacts, skipped 20 empty rows
Processing sheet: cxo_leads
Sheet 'cxo_leads': Processed 800 rows, extracted 780 contacts, skipped 20 empty rows
Total contacts to process: 2260
Split into 23 batches
Batch 1: Imported 100/100 contacts
Batch 2: Imported 100/100 contacts
...
================================================================================
IMPORT SUMMARY
================================================================================
Total rows: 2260
Processed: 2260
Imported: 2240
Errors: 0
Batches: 23
Duration: 45.32 seconds
Rate: 49.87 contacts/second
================================================================================
Import completed successfully!
```

## Logs

Import progress and errors are logged to:
```
logs/batch_import_YYYYMMDD_HHMMSS.log
```

Each log file contains:
- Detailed progress for each batch
- Error messages for failed imports
- Summary statistics
- Timing information

## Best Practices

### For Large Files (2000+ records):

1. **Use Appropriate Batch Size**
   - 100-200 records per batch for files with 2000-5000 records
   - 50-100 records per batch for files with 5000+ records

2. **Optimize Thread Count**
   - 4-8 threads for most systems
   - Increase to 8-16 if you have a powerful machine
   - Monitor CPU usage and adjust accordingly

3. **Use Dry Run First**
   - Always run with `--dry-run` first to preview
   - Check the preview counts before committing

4. **Import Only New**
   - Use `--import-only-new` to avoid updating existing contacts
   - Faster and safer for large imports

5. **Monitor Logs**
   - Check log files for errors
   - Review summary statistics after completion

### For Multiple Sheets:

1. **Process All Sheets**
   - Leave "Sheet Name" empty to process all sheets
   - Each sheet's contacts will be tagged with the sheet name

2. **Process Specific Sheet**
   - Specify sheet name to process only that sheet
   - Useful for testing or selective imports

## Troubleshooting

### Import Fails with Memory Error

- Reduce batch size (try 50 or 25)
- Reduce thread count (try 2 or 1)
- Process sheets individually instead of all at once

### Import is Slow

- Increase thread count (try 8 or 16)
- Increase batch size (try 200 or 500)
- Check system resources (CPU, memory, disk)

### Some Records Not Imported

- Check log file for error messages
- Verify Excel file format (headers, data types)
- Ensure required fields (name, email, or phone) are present

### Process Hangs

- Check if process is still running (check process ID)
- Review log file for last processed batch
- Restart import with smaller batch size

## API Endpoints

Super users can also use the Admin API endpoints:

### Run Batch Import

```http
POST /api/admin/scripts/import-contacts
Content-Type: application/json

{
  "excel_file": "data/the_ai_company.xlsx",
  "batch_size": 100,
  "threads": 4,
  "update_existing": false,
  "import_only_new": true,
  "sheet": null,
  "dry_run": false
}
```

### Get System Info

```http
GET /api/admin/system/info
```

### List Available Scripts

```http
GET /api/admin/scripts/list
```

### Run Custom Script

```http
POST /api/admin/scripts/run
Content-Type: application/json

{
  "script": "import_contacts_batch.py",
  "args": ["data/file.xlsx"],
  "kwargs": {
    "batch_size": 100,
    "threads": 4
  }
}
```

## Security

- Admin Tools are **only accessible to super users**
- All API endpoints require authentication and super user privileges
- Scripts run with the same permissions as the Flask application
- Logs are stored locally and contain no sensitive data

## Support

For issues or questions:
1. Check log files in `logs/` directory
2. Review error messages in the Admin Tools interface
3. Check system resources (memory, disk space)
4. Verify Excel file format and data quality















