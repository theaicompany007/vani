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
                
                # Add data rows
                for target in targets:
                    if target:  # Skip empty targets
                        row = [str(target.get(header, '')) for header in headers]
                        worksheet.append_row(row)
            
            logger.info(f"Exported {len(targets)} targets to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export targets: {str(e)}")
            return False
    
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


