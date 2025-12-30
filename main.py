import json
import os
import time
from core.gemini_brain import GeminiBrain
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient

def main():
    print("🚀 SEO Orchestrator Starting...")
    
    # Check for service account
    if not os.path.exists('config/service_account.json'):
         print("❌ Error: 'config/service_account.json' missing. accessing Google Sheets will fail.")
         print("Please download it from Google Cloud Console and place it in the config folder.")
         return

    # Initialize Brain
    try:
        brain = GeminiBrain()
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return

    # Load sites
    with open('config/sites.json', 'r') as f:
        sites = json.load(f)
    
    for site in sites:
        print(f"\nProcessing Site: {site.get('site_name', 'Unknown')}")
        
        # Init Sheets
        try:
            sheets = SheetsClient('config/service_account.json')
            pending_keywords = sheets.get_pending_rows(site['spreadsheet_id'])
            print(f"Found {len(pending_keywords)} pending keywords.")
        except Exception as e:
            print(f"❌ Error accessing sheets for {site['site_name']}: {e}")
            continue

        # Init WordPress
        wp = WordPressClient(
            site['wordpress_url'],
            site['wordpress_username'],
            site['wordpress_app_password']
        )
        if not wp.verify_auth():
            print(f"❌ Error: Cannot authenticate with WordPress for {site['site_name']}")
            continue

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            print(f"  👉 Working on: {keyword}")

            # 1. Research & Draft
            print("     Researching and Drafting (Gemini)...")
            draft = brain.research_and_draft(keyword)

            # 2. Refine (Persona)
            print("     Refining with Persona...")
            final_content = brain.refine_with_persona(draft, site['persona_prompt'])

            # 3. Images (Stubbed - Now Active)
            print("     Generating Images...")
            image_prompt = brain.generate_image_prompts(final_content)
            images_b64 = brain.generate_images(image_prompt)
            print(f"     [Image Generated]: {len(images_b64)} images")
            
            featured_media_id = None
            if images_b64:
                 try:
                     import base64
                     # Take the first image
                     image_data = base64.b64decode(images_b64[0])
                     # Upload to WP
                     print("     Uploading Image to WordPress...")
                     # Create a slug from keyword for filename
                     slug = keyword.replace(" ", "-").lower()[:50]
                     media_id, media_url = wp.upload_media(image_data, f"{slug}-cover.png")
                     if media_id:
                         featured_media_id = media_id
                         print(f"     ✅ Image Uploaded! ID: {media_id}")
                 except Exception as img_err:
                     print(f"     ❌ Image processing failed: {img_err}")

            # 4. Post to WP
            print("     Posting to WordPress...")
            user_title = keyword.title()
            try:
                post = wp.create_post(
                    title=user_title,
                    content=final_content,
                    featured_media_id=featured_media_id,
                    status='draft' # Safety first
                )
                link = post.get('link')
                print(f"     ✅ Posted! Link: {link}")
                
                # 5. Update Sheet
                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")
                print("     ✅ Sheet updated.")
            except Exception as e:
                print(f"     ❌ Failed to post/update: {e}")

if __name__ == "__main__":
    main()
