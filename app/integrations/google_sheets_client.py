"""Google Sheets import/export integration"""
import os
import logging
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Google Sheets client wrapper"""
    
    def __init__(self):
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        
        if not credentials_path or not spreadsheet_id:
            raise ValueError("Google Sheets credentials not found in environment variables")
        
        # Authenticate with service account
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        
        self.targets_sheet_name = os.getenv('GOOGLE_SHEETS_TARGETS_SHEET_NAME', 'Targets')
        self.activities_sheet_name = os.getenv('GOOGLE_SHEETS_ACTIVITIES_SHEET_NAME', 'Activities')
    
    def import_targets(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Import targets from Google Sheets
        
        Args:
            sheet_name: Optional sheet name. If not provided, uses default from env var or "Targets"
        
        Returns:
            List of target dictionaries
        """
        try:
            # Use provided sheet name or fall back to default
            target_sheet = sheet_name or self.targets_sheet_name
            
            # Check if worksheet exists
            try:
                worksheet = self.spreadsheet.worksheet(target_sheet)
            except gspread.exceptions.WorksheetNotFound:
                raise ValueError(f'Worksheet "{target_sheet}" not found in spreadsheet')
            
            records = worksheet.get_all_records()
            
            # Filter out empty rows
            records = [r for r in records if r and any(str(v).strip() for v in r.values() if v)]
            
            if not records:
                raise ValueError(f'No data found in "{target_sheet}" sheet')
            
            logger.info(f"Imported {len(records)} targets from Google Sheets (sheet: {target_sheet})")
            return records
            
        except Exception as e:
            logger.error(f"Failed to import targets: {str(e)}")
            raise
    
    def list_sheets(self) -> List[str]:
        """
        List all available sheet names in the spreadsheet
        
        Returns:
            List of sheet names
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            return [ws.title for ws in worksheets]
        except Exception as e:
            logger.error(f"Failed to list sheets: {str(e)}")
            raise
    
    def export_targets(self, targets: List[Dict[str, Any]]) -> bool:
        """
        Export targets to Google Sheets
        
        Args:
            targets: List of target dictionaries
            
        Returns:
            Success status
            
        Raises:
            Exception: If export fails, raises exception with error details
        """
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(self.targets_sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=self.targets_sheet_name,
                    rows=1000,
                    cols=20
                )
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare headers
            if targets and len(targets) > 0:
                headers = list(targets[0].keys())
                worksheet.append_row(headers)
                
                # Add data rows in batches to avoid rate limits
                # Google Sheets API allows 60 write requests per minute per user
                # We'll batch rows to minimize API calls
                batch_size = 100  # Process in batches
                total_batches = (len(targets) + batch_size - 1) // batch_size
                
                for batch_idx, i in enumerate(range(0, len(targets), batch_size)):
                    batch = targets[i:i + batch_size]
                    batch_rows = []
                    
                    for target in batch:
                        if target:  # Skip empty targets
                            row = [str(target.get(header, '')) for header in headers]
                            batch_rows.append(row)
                    
                    # Use batch update for better performance and rate limit management
                    if batch_rows:
                        try:
                            worksheet.append_rows(batch_rows)
                            logger.debug(f"Exported batch {batch_idx + 1}/{total_batches} ({len(batch_rows)} rows)")
                        except Exception as batch_error:
                            # If batch update fails, try individual rows
                            logger.warning(f"Batch update failed, falling back to individual rows: {batch_error}")
                            for row in batch_rows:
                                worksheet.append_row(row)
            
            logger.info(f"Exported {len(targets)} targets to Google Sheets")
            return True
            
        except Exception as e:
            error_str = str(e)
            error_dict = {}
            
            # Try to extract error details if it's a Google API error
            # gspread wraps Google API errors, so check for nested error info
            if hasattr(e, 'response'):
                try:
                    if hasattr(e.response, 'json'):
                        error_dict = e.response.json()
                    elif hasattr(e.response, 'text'):
                        import json
                        error_dict = json.loads(e.response.text)
                except:
                    pass
            
            # Also check if error has error_info attribute (gspread style)
            if hasattr(e, 'error_info'):
                error_dict = e.error_info
            
            # Log the full error
            logger.error(f"Failed to export targets: {error_str}")
            if error_dict:
                logger.error(f"Error details: {error_dict}")
            
            # Re-raise with error details preserved
            # Format error message to include details for API to parse
            if error_dict:
                error_msg = f"{error_str} | Details: {error_dict}"
            else:
                error_msg = error_str
            
            # Create a new exception with the formatted message
            new_exception = Exception(error_msg)
            # Attach original error details as attribute for API to access
            new_exception.error_details = error_dict
            raise new_exception
    
    def export_activities(self, activities: List[Dict[str, Any]]) -> bool:
        """
        Export activities to Google Sheets
        
        Args:
            activities: List of activity dictionaries
            
        Returns:
            Success status
        """
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(self.activities_sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=self.activities_sheet_name,
                    rows=10000,
                    cols=20
                )
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare headers
            if activities:
                headers = list(activities[0].keys())
                worksheet.append_row(headers)
                
                # Add data rows
                for activity in activities:
                    row = [activity.get(header, '') for header in headers]
                    worksheet.append_row(row)
            
            logger.info(f"Exported {len(activities)} activities to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export activities: {str(e)}")
            return False


