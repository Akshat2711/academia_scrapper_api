import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
import time

load_dotenv()

class SRMPortalScraper:
    """Robust SRM Student Portal scraper with improved error handling and waiting"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.browser = None
        self.page = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"[WARNING] Error during cleanup: {str(e)}")
    
    async def scrape_data(self) -> dict:
        """Main method to scrape and return all data as dictionary"""
        try:
            await self._initialize_browser()
            await self._login()
            await self._navigate_to_attendance()
            data = await self._extract_data()
            return data
        except Exception as e:
            print(f"[ERROR] An error occurred during scraping: {str(e)}")
            raise
        finally:
            await self.cleanup()
    
    async def _initialize_browser(self):
        """Initialize browser and page"""
        print("[INFO] Initializing browser...")
        self.playwright = await async_playwright().start()
        
        # Launch browser with more robust settings
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create page with proper viewport
        self.page = await self.browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )
        
        # Set longer timeouts
        self.page.set_default_timeout(30000)  # 30 seconds
        self.page.set_default_navigation_timeout(60000)  # 60 seconds
        
        print("[INFO] Browser initialized successfully")
    
    async def _login(self):
        """Handle login process with better error handling"""
        print("[INFO] Starting login process...")
        
        # Navigate to login page with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Login attempt {attempt + 1}/{max_retries}")
                await self.page.goto("https://academia.srmist.edu.in/", 
                                   wait_until="networkidle", 
                                   timeout=60000)
                break
            except PlaywrightTimeoutError:
                if attempt == max_retries - 1:
                    raise Exception("Failed to load login page after multiple attempts")
                print(f"[WARNING] Login page load attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2)
        
        # Wait for iframe to load
        print("[INFO] Waiting for login iframe...")
        try:
            await self.page.wait_for_selector(".siginiframe", state="attached", timeout=30000)
            iframe = self.page.frame_locator(".siginiframe")
            
            # Enter email
            print("[INFO] Entering email...")
            await iframe.locator("input#login_id").wait_for(state="visible", timeout=10000)
            await iframe.locator("input#login_id").fill(self.email)
            
            # Click next button
            print("[INFO] Clicking next button...")
            await iframe.locator("#nextbtn").click()
            
            # Wait a bit for the password field to appear
            await asyncio.sleep(2)
            
            # Enter password
            print("[INFO] Entering password...")
            await iframe.locator("input#password").wait_for(state="visible", timeout=10000)
            await iframe.locator("input#password").fill(self.password)
            
            # Click final login button
            print("[INFO] Clicking login button...")
            await iframe.locator("#nextbtn").click()
            
            # Wait for login to complete - look for welcome page indicators
            print("[INFO] Waiting for successful login...")
            await asyncio.sleep(5)
            
            # Check if we're on the welcome page by looking for specific elements
            try:
                await self.page.wait_for_function(
                    "window.location.hash.includes('WELCOME') || document.querySelector('.mainDiv')",
                    timeout=30000
                )
                print("[INFO] Login successful!")
            except PlaywrightTimeoutError:
                raise Exception("Login may have failed - didn't reach welcome page")
                
        except PlaywrightTimeoutError as e:
            raise Exception(f"Login failed - timeout waiting for elements: {str(e)}")
    
    async def _navigate_to_attendance(self):
        """Navigate to attendance page with robust waiting"""
        print("[INFO] Navigating to attendance page...")
        
        max_retries = 1
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Navigation attempt {attempt + 1}/{max_retries}")
                
                # Navigate to attendance page
                await self.page.goto(
                    "https://academia.srmist.edu.in/#Page:My_Attendance", 
                    wait_until="networkidle",
                    timeout=60000
                )
                
                # Wait for main content to load
                print("[INFO] Waiting for attendance page content...")
                await self.page.wait_for_selector(".mainDiv", state="attached", timeout=30000)
                
                # Scroll into view to trigger any lazy loading
                await self.page.locator(".mainDiv").scroll_into_view_if_needed()
                
                # Wait for tables to load - attendance data is in tables
                print("[INFO] Waiting for data tables...")
                await self.page.wait_for_selector("table", state="attached", timeout=20000)
                
                # Additional wait to ensure all dynamic content loads
                await asyncio.sleep(5)
                
                # Verify we have the expected tables
                table_count = await self.page.locator("table").count()
                print(f"[INFO] Found {table_count} tables on the page")
                
                if table_count >= 3:  # We expect at least student info, attendance, and marks tables
                    print("[INFO] Successfully loaded attendance page with data")
                    break
                else:
                    print(f"[WARNING] Expected at least 3 tables, found {table_count}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Insufficient tables found: {table_count}")
                    
            except PlaywrightTimeoutError:
                if attempt == max_retries - 1:
                    raise Exception("Failed to load attendance page after multiple attempts")
                print(f"[WARNING] Attendance page load attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(3)
    
    async def _extract_data(self) -> dict:
        """Extract and parse all data from the page"""
        print("[INFO] Extracting attendance data...")
        
        try:
            # Get the main div content
            html_content = await self.page.locator(".mainDiv").inner_html()
            
            # Parse the data
            data = self._parse_all_data(html_content)
            print("[INFO] Data extraction completed successfully")
            return data
            
        except Exception as e:
            print(f"[ERROR] Failed to extract data: {str(e)}")
            
            # Debug: Save page content for analysis
            try:
                page_content = await self.page.content()
                with open("debug_page_content.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
                print("[DEBUG] Page content saved to debug_page_content.html")
            except Exception as debug_error:
                print(f"[DEBUG] Could not save debug content: {debug_error}")
            
            raise
    
    def _parse_all_data(self, html_content: str) -> dict:
        """Parse HTML content and extract structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')
        
        print(f"[DEBUG] Total tables found: {len(tables)}")
        
        if len(tables) < 3:
            print("[ERROR] Insufficient tables found. Page structure may have changed.")
            # Save HTML for debugging
            with open("debug_html_content.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            raise ValueError(f"Expected at least 3 tables but found {len(tables)}. Debug HTML saved.")
        
        # Find the correct tables by analyzing their structure
        student_info_table = None
        attendance_table = None
        marks_table = None
        
        for i, table in enumerate(tables):
            table_text = table.get_text().lower()
            
            # Student info table has registration number
            if 'registration number' in table_text and not student_info_table:
                student_info_table = table
                print(f"[DEBUG] Student info table found at index {i}")
            
            # Attendance table has course codes and hours conducted
            elif 'hours conducted' in table_text and 'course code' in table_text and not attendance_table:
                attendance_table = table
                print(f"[DEBUG] Attendance table found at index {i}")
            
            # Marks table has test performance
            elif 'test performance' in table_text and not marks_table:
                marks_table = table
                print(f"[DEBUG] Marks table found at index {i}")
        
        if not student_info_table:
            raise ValueError("Could not find student information table")
        if not attendance_table:
            raise ValueError("Could not find attendance table")
        
        result = {
            'student_info': self._parse_student_info(student_info_table),
            'attendance': self._parse_attendance(attendance_table),
            'summary': {}
        }
        
        # Marks table might be empty, so make it optional
        if marks_table:
            result['marks'] = self._parse_marks(marks_table)
            print("[INFO] Marks data parsed successfully")
        else:
            result['marks'] = {}
            print("[WARNING] No marks table found - marks data unavailable")
        
        return result
    
    def _parse_student_info(self, table) -> dict:
        """Parse student basic information"""
        info = {}
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).rstrip(':').lower().replace(' ', '_')
                
                if key == 'photo-id':
                    img_tag = cells[1].find('img')
                    info['photo_url'] = img_tag['src'] if img_tag else ""
                else:
                    value = cells[1].get_text(strip=True)
                    info[key] = value
        
        # Clean up enrollment data
        if 'enrollment_status_/_doe' in info:
            enrollment = info.pop('enrollment_status_/_doe')
            if ' / ' in enrollment:
                info['enrollment_status'], info['enrollment_date'] = enrollment.split(' / ')
            else:
                info['enrollment_status'] = enrollment
                info['enrollment_date'] = ""
        
        print(f"[DEBUG] Parsed student info for: {info.get('name', 'Unknown')}")
        return info
    
    def _parse_attendance(self, table) -> dict:
        """Parse attendance data with improved error handling"""
        attendance = {}
        rows = table.find_all('tr')[1:]  # Skip header
        
        total_conducted = 0
        total_absent = 0
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 9:
                try:
                    # Get course code (remove any HTML like <br> tags)
                    course_code_html = str(cells[0])
                    course_code = cells[0].get_text(strip=True).split('\n')[0]
                    
                    # Parse numeric values safely
                    hours_conducted_text = cells[6].get_text(strip=True)
                    hours_absent_text = cells[7].get_text(strip=True)
                    
                    hours_conducted = int(hours_conducted_text) if hours_conducted_text.isdigit() else 0
                    hours_absent = int(hours_absent_text) if hours_absent_text.isdigit() else 0
                    
                    # Extract attendance percentage
                    att_text = cells[8].get_text(strip=True)
                    att_matches = re.findall(r'\d+\.\d+', att_text)
                    att_percentage = float(att_matches[0]) if att_matches else 0.0
                    
                    attendance[course_code] = {
                        'course_title': cells[1].get_text(strip=True),
                        'category': cells[2].get_text(strip=True),
                        'faculty_name': cells[3].get_text(strip=True),
                        'slot': cells[4].get_text(strip=True),
                        'room_no': cells[5].get_text(strip=True),
                        'hours_conducted': hours_conducted,
                        'hours_absent': hours_absent,
                        'attendance_percentage': att_percentage
                    }
                    
                    total_conducted += hours_conducted
                    total_absent += hours_absent
                    
                except (ValueError, IndexError) as e:
                    print(f"[WARNING] Error parsing attendance row: {e}")
                    continue
        
        # Calculate overall attendance
        overall_percentage = 0.0
        if total_conducted > 0:
            overall_percentage = round(((total_conducted - total_absent) / total_conducted) * 100, 2)
        
        print(f"[DEBUG] Parsed attendance for {len(attendance)} courses")
        
        return {
            'courses': attendance,
            'overall_attendance': overall_percentage,
            'total_hours_conducted': total_conducted,
            'total_hours_absent': total_absent
        }
    
    def _parse_marks(self, table) -> dict:
        """Parse marks data with improved error handling"""
        marks = {}
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                try:
                    course_code = cells[0].get_text(strip=True)
                    course_type = cells[1].get_text(strip=True)
                    
                    tests = []
                    nested_table = cells[2].find('table')
                    
                    if nested_table:
                        font_tags = nested_table.find_all('font')
                        for font_tag in font_tags:
                            try:
                                font_html = str(font_tag)
                                
                                if '<br' in font_html and '/' in font_html:
                                    strong_tag = font_tag.find('strong')
                                    if strong_tag:
                                        strong_text = strong_tag.get_text(strip=True)
                                        if '/' in strong_text:
                                            test_name, max_marks_str = strong_text.split('/')
                                            max_marks = float(max_marks_str.strip())
                                            
                                            # Extract obtained marks after <br>
                                            br_split = font_html.split('<br')
                                            if len(br_split) > 1:
                                                after_br = br_split[1].split('>', 1)[1] if '>' in br_split[1] else br_split[1]
                                                obtained_text = after_br.replace('</font>', '').strip()
                                                
                                                if obtained_text:
                                                    obtained_marks = float(obtained_text)
                                                    percentage = round((obtained_marks / max_marks) * 100, 2) if max_marks > 0 else 0
                                                    
                                                    tests.append({
                                                        'test_name': test_name.strip(),
                                                        'obtained_marks': obtained_marks,
                                                        'max_marks': max_marks,
                                                        'percentage': percentage
                                                    })
                            except (ValueError, IndexError, AttributeError):
                                continue
                    
                    marks[course_code] = {
                        'course_type': course_type,
                        'tests': tests
                    }
                
                except (ValueError, IndexError) as e:
                    print(f"[WARNING] Error parsing marks row: {e}")
                    continue
        
        print(f"[DEBUG] Parsed marks for {len(marks)} courses")
        return marks

# Async context manager usage
async def get_srm_data(email: str, password: str) -> dict:
    """Get SRM student data as dictionary using context manager"""
    async with SRMPortalScraper(email, password) as scraper:
        return await scraper.scrape_data()

# Main execution
async def main():
    email = os.getenv("SRM_EMAIL")
    password = os.getenv("SRM_PASSWORD")
    
    if not email or not password:
        print("[ERROR] Please set SRM_EMAIL and SRM_PASSWORD in your .env file")
        return
    
    try:
        print("[INFO] Starting SRM portal scraping...")
        data = await get_srm_data(email, password)
        
        # Print complete data dictionary
        print("\n" + "="*50)
        print("COMPLETE STUDENT DATA")
        print("="*50)
        
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"[ERROR] Failed to scrape data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())