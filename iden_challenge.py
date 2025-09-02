import json
import os
import time
import signal
import sys
from typing import List, Dict, Set, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError, Page, BrowserContext, Browser

# ============================================================================
# CONFIGURATION
# ============================================================================
SESSION_FILE = "session.json"
PRODUCTS_FILE = "products.json"

# Performance flags
VERBOSE = False
SAVE_BATCH_SIZE = 50  # save every N new products
BACKUP_DONE = False   # ensure we back up at most once per run

EMAIL = "sneha.g.s@campusuvce.in"
PASSWORD = "8D2g2xCT"
APP_URL = "https://hiring.idenhq.com/"

HEADERS = [
    "item_#", "cost", "sku", "details", "product",
    "dimensions", "weight_(kg)", "type"
]

def vprint(msg: str) -> None:
    if VERBOSE:
        print(msg)

# ============================================================================
# SIGNAL HANDLING
# ============================================================================
def signal_handler(signum, frame):
    """Handle interruption signals gracefully."""
    try:
        current_products = load_existing_products()
        print(f"\n⏹️ SIGNAL RECEIVED: Total products saved: {len(current_products)}")
    except:
        print(f"\n⏹️ SIGNAL RECEIVED: Could not determine total products saved")
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        print("📡 Signal handlers configured")
    except Exception as e:
        print(f"⚠️ Could not setup signal handlers: {e}")

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================
def save_session(context: BrowserContext) -> None:
    """Save browser session state for future reuse."""
    try:
        context.storage_state(path=SESSION_FILE)
        print(f"✅ Session saved to {SESSION_FILE}")
    except Exception as e:
        print(f"❌ Failed to save session: {e}")
        raise

def load_session_if_exists() -> Optional[str]:
    """Check if a valid session file exists."""
    if os.path.exists(SESSION_FILE):
        try:
            # Validate session file is readable JSON
            with open(SESSION_FILE, 'r') as f:
                json.load(f)
            return SESSION_FILE
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Corrupted session file: {e}")
            os.remove(SESSION_FILE)
    return None

def get_page_with_session(p) -> tuple[Page, BrowserContext, Browser]:
    """
    Smart session management: load existing session or create new one.
    """
    browser = p.chromium.launch(headless=False)
    context = None

    session_file = load_session_if_exists()
    
    if session_file:
        try:
            print("🔄 Using existing session...")
            context = browser.new_context(storage_state=session_file)
            page = context.new_page()
            page.goto(APP_URL)
            
            # Check if session is still valid
            try:
                page.wait_for_selector("text=Menu", timeout=5000)
                print("✅ Existing session is valid")
                return page, context, browser
            except PWTimeoutError:
                print("⚠️ Session expired, creating new login")
                context.close()
                os.remove(session_file)
                
        except Exception as e:
            print(f"❌ Failed to load session: {e}")
            if os.path.exists(session_file):
                os.remove(session_file)

    # Create new session
    print("🆕 Creating new session...")
    context = browser.new_context()
    
    # Add browser close detection
    def on_browser_disconnected():
        try:
            current_products = load_existing_products()
            print(f"\n🌐 BROWSER CLOSED: Total products saved: {len(current_products)}")
        except:
            print(f"\n🌐 BROWSER CLOSED: Could not determine total products saved")
    
    browser.on("disconnected", on_browser_disconnected)
    
    page = context.new_page()
    page.goto(APP_URL)
    
    # Wait for page to load and perform login
    page.wait_for_load_state("domcontentloaded")
    login(page)
    save_session(context)

    return page, context, browser

# ============================================================================
# SMART LOGIN WITH ROBUST ERROR HANDLING
# ============================================================================
def login(page: Page) -> None:
    """
    Robust login function with smart waiting and comprehensive error handling.
    """
    try:
        print("🔐 Starting login process...")
        
        # Wait for login form to be ready
        page.wait_for_selector("input[type='email']", timeout=15000)
        page.wait_for_selector("input[type='password']", timeout=15000)
        
        # Fill credentials with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Clear and fill email
                email_input = page.locator("input[type='email']").first
                email_input.clear()
                email_input.fill(EMAIL)
                
                # Clear and fill password
                password_input = page.locator("input[type='password']").first
                password_input.clear()
                password_input.fill(PASSWORD)
                
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fill credentials after {max_retries} attempts: {e}")
                print(f"⚠️ Attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
        
        # Wait for sign-in button and click
        signin_button = page.locator("button:has-text('Sign in')").first
        signin_button.wait_for(state="visible", timeout=10000)
        signin_button.click()
        
        # Wait for successful login (Menu button appears)
        page.wait_for_selector("text=Menu", timeout=20000)
        
        print("✅ Login successful")
        
    except PWTimeoutError as e:
        print(f"❌ Login timeout: {e}")
        raise RuntimeError("❌ Login failed: Timeout waiting for elements")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise RuntimeError(f"❌ Login failed: {e}")

# ============================================================================
# INTELLIGENT NAVIGATION WITH SMART WAITING
# ============================================================================
def navigate_to_products(page: Page) -> None:
    """
    Navigate to product table with intelligent waiting and error handling.
    """
    try:
        print("🧭 Starting navigation to product table...")
        
        # Step 1: Click Menu button
        menu_button = page.locator("text=Menu").first
        menu_button.wait_for(state="visible", timeout=10000)
        menu_button.click()
        print("✅ Clicked Menu button")
        
        # Wait for menu to expand
        page.wait_for_timeout(1000)
        
        # Step 2: Click Data Management
        data_mgmt = page.locator("text=Data Management").first
        data_mgmt.wait_for(state="visible", timeout=10000)
        data_mgmt.click()
        print("✅ Clicked Data Management")
        
        # Wait for submenu
        page.wait_for_timeout(1000)
        
        # Step 3: Click Inventory
        inventory = page.locator("text=Inventory").first
        inventory.wait_for(state="visible", timeout=10000)
        inventory.click()
        print("✅ Clicked Inventory")
        
        # Wait for submenu
        page.wait_for_timeout(1000)
        
        # Step 4: Click View All Products
        view_products = page.locator("text=View All Products").first
        view_products.wait_for(state="visible", timeout=10000)
        view_products.click()
        print("✅ Clicked View All Products")
        
        # Wait for table to load
        page.wait_for_timeout(3000)
        page.wait_for_selector("table, div[role='table']", timeout=20000)
        
        # Take screenshot for verification
        page.screenshot(path="after_navigation.png")
        print("📸 Screenshot saved as after_navigation.png")
        print("✅ Successfully reached product table")
        
    except Exception as e:
        print(f"❌ Navigation failed: {e}")
        raise RuntimeError(f"❌ Navigation failed: {e}")

# ============================================================================
# DATA VALIDATION AND DEDUPLICATION
# ============================================================================
def validate_product_data(product: Dict) -> bool:
    """Validate product data integrity."""
    try:
        # Check all required fields exist
        for header in HEADERS:
            if header not in product:
                return False
        
        # Check item_# is numeric
        try:
            int(product["item_#"])
        except ValueError:
            return False
        
        # Check SKU format
        if not product["sku"] or len(product["sku"]) < 3:
            return False
            
        return True
    except Exception:
        return False

def load_existing_products(filename: str = PRODUCTS_FILE) -> List[Dict]:
    """Load existing products with validation."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                products = json.load(f)
                print(f"✅ Loaded {len(products)} existing products")
                
                # Validate existing data
                valid_products = [p for p in products if validate_product_data(p)]
                if len(valid_products) != len(products):
                    print(f"⚠️ Filtered out {len(products) - len(valid_products)} invalid products")
                
                return valid_products
        except Exception as e:
            print(f"❌ Failed to load existing products: {e}")
            return []
    return []

def save_products_to_json(products: List[Dict], filename: str = PRODUCTS_FILE) -> None:
    """Save products with error handling and backup."""
    try:
        global BACKUP_DONE
        # Create backup only once per run
        if not BACKUP_DONE and os.path.exists(filename):
            backup_name = f"{filename}.backup"
            if os.path.exists(backup_name):
                os.remove(backup_name)
            os.rename(filename, backup_name)
            vprint(f"📦 Created backup: {backup_name}")
            BACKUP_DONE = True
        
        # Save new data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)
        
        vprint(f"✅ Saved {len(products)} products to {filename}")
        
    except Exception as e:
        print(f"❌ Failed to save products: {e}")
        # Restore backup if save failed
        if os.path.exists(f"{filename}.backup"):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                os.rename(f"{filename}.backup", filename)
                print("🔄 Restored backup file")
            except Exception as restore_error:
                print(f"❌ Failed to restore backup: {restore_error}")
        raise

# ============================================================================
# DYNAMIC PRODUCT SCRAPING
# ============================================================================
def scrape_products(page: Page, existing_products: List[Dict]) -> List[Dict]:
    """
    Dynamic product scraping that detects new products as you scroll.
    """
    products = existing_products.copy()
    existing_item_nums = {p["item_#"] for p in existing_products}
    existing_skus = {p["sku"] for p in existing_products}
    
    print(f"🔄 Starting with {len(existing_products)} existing products")
    print("📜 Scroll down to load more products - they will be saved automatically")
    
    last_row_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 500  # Allow more scrolling
    
    new_since_last_save = 0
    while scroll_attempts < max_scroll_attempts:
        try:
            # Proactively scroll to load more rows (both page and any scrollable containers)
            try:
                page.evaluate(
                    """
                    () => {
                        // Scroll window faster
                        window.scrollBy(0, Math.max(400, Math.floor(window.innerHeight * 1.2)));

                        // Try to scroll any overflowing containers (tables, grids, etc.)
                        const isScrollable = (el) => {
                            const style = window.getComputedStyle(el);
                            const overflowY = style.overflowY;
                            return (overflowY === 'auto' || overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
                        };
                        const candidates = Array.from(document.querySelectorAll('div,main,section,table,tbody,[role="table"],[role="rowgroup"]'))
                            .filter(isScrollable);
                        candidates.forEach(el => {
                            el.scrollTop = Math.min(el.scrollTop + Math.floor(el.clientHeight * 1.2), el.scrollHeight);
                        });
                    }
                    """
                )
            except Exception:
                pass
            # Bulk read visible rows with a single evaluation
            rows_data = page.evaluate(
                """
                () => {
                    const out = [];
                    const bodies = [
                        ...document.querySelectorAll('table tbody'),
                        ...document.querySelectorAll('div[role="table"] div[role="rowgroup"]')
                    ];
                    let trs = [];
                    for (const b of bodies) trs = trs.concat(Array.from(b.querySelectorAll('tr')));
                    if (trs.length === 0) trs = Array.from(document.querySelectorAll('tr'));
                    for (const tr of trs) {
                        const tds = tr.querySelectorAll('td');
                        const cells = Array.from(tds).map(td => td.innerText.trim());
                        if (cells.length >= 6) out.push(cells);
                    }
                    return out;
                }
                """
            )

            current_row_count = len(rows_data) if rows_data else 0
            vprint(f"📏 Current row count: {current_row_count}, Last known: {last_row_count}")
            
            if current_row_count > last_row_count:
                print(f"🆕 New rows detected: {last_row_count} → {current_row_count} (+{current_row_count - last_row_count})")
                
                # Process only the new rows
                new_products_found = 0
                for row_index in range(last_row_count, current_row_count):
                    try:
                        cells = rows_data[row_index] if rows_data and row_index < len(rows_data) else None
                        
                        if cells and len(cells) >= 6:
                            # Ensure we have the right number of cells
                            if len(cells) > len(HEADERS):
                                cells = cells[:len(HEADERS)]
                            elif len(cells) < len(HEADERS):
                                cells.extend([''] * (len(HEADERS) - len(cells)))
                            
                            product = dict(zip(HEADERS, cells))
                            vprint(f"📦 Product data: {product['item_#']} - {product['sku']}")
                            
                            # Check for duplicates (unique by item number only)
                            if product["item_#"] not in existing_item_nums:
                                if validate_product_data(product):
                                    products.append(product)
                                    existing_item_nums.add(product["item_#"])
                                    new_products_found += 1
                                    
                                    new_since_last_save += 1
                                    if new_since_last_save >= SAVE_BATCH_SIZE:
                                        save_products_to_json(products)
                                        print(f"✅ Saved {len(products)} products so far")
                                        new_since_last_save = 0
                                        
                                else:
                                    print(f"⚠️ Invalid product data: {product['item_#']}")
                                    continue
                            else:
                                vprint(f"🔄 Duplicate product: {product['item_#']}")
                                continue
                        else:
                            vprint(f"⚠️ Invalid cell count: {len(cells) if cells else 0}")
                            continue
                            
                    except Exception as e:
                        vprint(f"⚠️ Error processing row {row_index + 1}: {e}")
                        continue
                
                if new_products_found > 0:
                    print(f"🆕 Added {new_products_found} new products (Total: {len(products)})")
                    last_row_count = current_row_count
                    scroll_attempts = 0  # Reset scroll attempts when new products are found
                else:
                    vprint(f"ℹ️ No new products found in {current_row_count - last_row_count} new rows")
                    scroll_attempts += 1
                    # Try clicking Next more aggressively
                    if scroll_attempts % 3 == 0:
                        try:
                            next_btn = page.locator("button:has-text('Next'), a:has-text('Next'), [aria-label='Next']").first
                            if next_btn and next_btn.is_enabled():
                                next_btn.click()
                                time.sleep(0.5)
                                vprint("➡️ Clicked Next to load more")
                        except Exception:
                            pass
            else:
                scroll_attempts += 1
            
            # Wait before next check
            time.sleep(0.5)
            
        except Exception as e:
            vprint(f"⚠️ Error during scraping: {e}")
            scroll_attempts += 1
            time.sleep(1)
            continue
    
    # Final batch save if pending
    if new_since_last_save > 0:
        save_products_to_json(products)
        print(f"✅ Saved {len(products)} products so far")

    print(f"🏁 Scraping completed: {len(products)} total products")
    return products

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """
    Main execution function for dynamic product scraping.
    """
    print("🚀 Starting Dynamic Product Scraping")
    print("=" * 50)
    print("📜 SCROLL DOWN to load more products - they will be saved automatically")
    print("🌐 CLOSE BROWSER when you're done - script will show total products saved")
    print("=" * 50)
    
    try:
        with sync_playwright() as p:
            # Get page with session (login is handled here)
            page, context, browser = get_page_with_session(p)
            
            # Navigate to products
            navigate_to_products(page)
            
            # Load existing data
            existing_products = load_existing_products()
            print(f"📊 Loaded {len(existing_products)} existing products")
            print(f"📈 Starting from product #{len(existing_products) + 1}")
            
            # Start dynamic scraping
            print("🔄 Starting product detection...")
            print("💡 Scroll down to load more products!")
            
            products = scrape_products(page, existing_products)
            
            # Final save
            save_products_to_json(products)
            
            # Show final results
            print("=" * 50)
            print("🎯 FINAL RESULTS:")
            print(f"📦 Total Products: {len(products)}")
            
            browser.close()
            print("🎉 Scraping completed successfully!")
            print(f"✅ Total products saved: {len(products)}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
        try:
            current_products = load_existing_products()
            print(f"📊 Total products saved so far: {len(current_products)}")
        except:
            print("📊 Could not determine total products saved")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        try:
            current_products = load_existing_products()
            print(f"📊 Total products saved before error: {len(current_products)}")
        except:
            print("📊 Could not determine total products saved")
        raise
    finally:
        print("🏁 Process finished")
        try:
            final_products = load_existing_products()
            if final_products:
                print(f"📊 FINAL COUNT: Total products in JSON file: {len(final_products)}")
        except:
            pass

if __name__ == "__main__":
    setup_signal_handlers()  # Setup signal handlers
    main()
