import json
import os
import base64
from core.gemini_brain import GeminiBrain
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient

def main():
    print("🚀 SEO Orchestrator (Multi-Tenant Architecture) Starting...")
    
    # Check for service account
    if not os.path.exists('config/service_account.json'):
         print("❌ Error: 'config/service_account.json' missing.")
         return

    # Load sites configuration
    with open('config/sites.json', 'r') as f:
        sites = json.load(f)
    
    for site in sites:
        company_id = site.get('company_id', 'default')
        site_name = site.get('site_name', 'Unknown')
        
        print(f"\n{'='*80}")
        print(f"🏢 Processing Company: {site_name} (ID: {company_id})")
        print(f"{'='*80}")
        
        # Initialize Brain with company-specific knowledge base
        kb_path = f"config/companies/{company_id}/knowledge_base"
        try:
            brain = GeminiBrain(knowledge_base_path=kb_path)
            print(f"✅ Brain initialized for '{company_id}' with KB path: {kb_path}")
        except Exception as e:
            print(f"❌ Error initializing Gemini for '{company_id}': {e}")
            continue
        
        # Init Sheets
        try:
            sheets = SheetsClient('config/service_account.json')
            pending_keywords = sheets.get_pending_rows(site['spreadsheet_id'])
            
            # Fetch Inventory for Internal Linking
            print("     Fetching Article Inventory for Link Building...")
            inventory = sheets.get_all_completed_articles(site['spreadsheet_id'])
            print(f"     Found {len(inventory)} existing articles to potential link to.")
            
            print(f"Found {len(pending_keywords)} pending keywords to write.")
        except Exception as e:
            print(f"❌ Error accessing sheets: {e}")
            continue

        # Init WordPress
        wp = WordPressClient(
            site['wordpress_url'],
            site['wordpress_username'],
            site['wordpress_app_password']
        )
        if not wp.verify_auth():
            print(f"❌ Error: Cannot authenticate with WordPress.")
            continue

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            print(f"\n👉 Working on Keyword: {keyword}")

            try:
                # ---------------------------------------------------------
                # STEP 1: ANALYST (Plan & Structure)
                # ---------------------------------------------------------
                print("     1. Analyst Agent: Creating Strategic Outline...")
                outline_json = brain.analyze_and_plan(keyword, inventory)
                final_title = outline_json.get('title', keyword.title())
                print(f"        Title Idea: {final_title}")

                # ---------------------------------------------------------
                # STEP 2: WRITER (Drafting)
                # ---------------------------------------------------------
                print("     2. Senior Writer Agent: Writing Content...")
                draft_html = brain.write_article_body(outline_json)

                # ---------------------------------------------------------
                # STEP 3: HUMANIZADOR TRI (Voz do Marcelo Jesus)
                # ---------------------------------------------------------
                print("     3. Humanizer Agent: Injecting TRI Voice & Personality...")
                humanized_html = brain.humanize_with_tri_voice(draft_html)

                # ---------------------------------------------------------
                # STEP 4: EDITOR (Conversion & Polishing)
                # ---------------------------------------------------------
                print("     4. Editor Agent: Polishing & SEO Local Check...")
                final_content = brain.edit_and_refine(humanized_html)

                # ---------------------------------------------------------
                # STEP 5: VISUAL (Images - Editorial Premium)
                # ---------------------------------------------------------
                print("     5. Visual Agent: Generating Editorial Images...")
                prompts_str = brain.generate_image_prompts(final_content)
                
                # Now returns 2 prompts (Capa + Final) separated by |||
                prompts_list = [p.strip() for p in prompts_str.split('|||') if p.strip()]
                
                featured_media_id = None
                slug = keyword.replace(" ", "-").lower()[:30]
                
                # ---- IMAGE 1: AI-Generated Cover (Featured Image) ----
                if len(prompts_list) >= 1:
                    print(f"        📷 Image 1 (Capa): Generating AI editorial image...")
                    b64_image = brain.generate_final_images(prompts_list[0])
                    
                    if b64_image:
                        image_data = base64.b64decode(b64_image)
                        filename = f"{slug}-capa.png"
                        media_id, media_url = wp.upload_media(image_data, filename)
                        featured_media_id = media_id
                        print(f"        ✅ Featured Image Set (ID: {media_id})")
                
                # ---- IMAGE 2: Real Author Photo (Rotation) ----
                print(f"        📸 Image 2 (Autor): Loading real author photo...")
                author_photo_data, author_photo_filename = brain.get_real_author_photo()
                
                if author_photo_data:
                    # Determine file extension for proper upload
                    ext = author_photo_filename.split('.')[-1].lower()
                    upload_filename = f"{slug}-terapeuta.{ext}"
                    media_id, media_url = wp.upload_media(author_photo_data, upload_filename)
                    
                    if media_url:
                        # Insert author photo into first placeholder
                        author_img_html = (
                            f"<figure class='wp-block-image aligncenter size-large'>"
                            f"<img src='{media_url}' alt='Marcelo Jesus - Terapeuta TRI em Moema, São Paulo'/>"
                            f"<figcaption>Marcelo Jesus — Terapeuta especialista em TRI | Consultório em Moema, SP</figcaption>"
                            f"</figure>"
                        )
                        
                        if "<!-- IMG_PLACEHOLDER -->" in final_content:
                            final_content = final_content.replace(
                                "<!-- IMG_PLACEHOLDER -->", 
                                author_img_html, 
                                1  # Replace only the FIRST placeholder
                            )
                            print(f"        ✅ Author photo injected into article body.")
                        else:
                            # No placeholder found - insert after first H2
                            import re as re_mod
                            h2_match = re_mod.search(r'(</h2>)', final_content)
                            if h2_match:
                                insert_pos = h2_match.end()
                                final_content = final_content[:insert_pos] + "\n" + author_img_html + "\n" + final_content[insert_pos:]
                                print(f"        ✅ Author photo inserted after first H2.")
                            else:
                                final_content += "\n" + author_img_html
                                print(f"        ✅ Author photo appended to end.")
                else:
                    print(f"        ⚠️ No author photos found. Skipping Image 2.")
                
                # ---- IMAGE 3: AI-Generated Final (Hope/Transformation) ----
                if len(prompts_list) >= 2:
                    print(f"        📷 Image 3 (Final): Generating AI editorial image...")
                    b64_image = brain.generate_final_images(prompts_list[1])
                    
                    if b64_image:
                        image_data = base64.b64decode(b64_image)
                        filename = f"{slug}-final.png"
                        media_id, media_url = wp.upload_media(image_data, filename)
                        
                        # Insert into remaining placeholder or append before CTA
                        final_img_html = f"<figure class='wp-block-image'><img src='{media_url}' alt='{final_title}'/></figure>"
                        
                        if "<!-- IMG_PLACEHOLDER -->" in final_content:
                            final_content = final_content.replace(
                                "<!-- IMG_PLACEHOLDER -->", 
                                final_img_html, 
                                1
                            )
                            print(f"        ✅ Final image injected into placeholder.")
                        else:
                            # Insert before CTA box if it exists
                            if '<div class="cta-box">' in final_content:
                                final_content = final_content.replace(
                                    '<div class="cta-box">',
                                    final_img_html + '\n<div class="cta-box">'
                                )
                                print(f"        ✅ Final image inserted before CTA.")
                            else:
                                final_content += "\n" + final_img_html
                                print(f"        ✅ Final image appended to end.")

                # ---------------------------------------------------------
                # POST TO WORDPRESS
                # ---------------------------------------------------------
                print("     Posting to WordPress (PUBLISH)...")
                
                # Extract meta description from plan (or fallback to intro snippet)
                meta_desc = outline_json.get('meta_description', "")
                if not meta_desc:
                     # Fallback: Clean HTML tags from first 160 chars of content
                     import re
                     clean = re.sub('<[^<]+?>', '', final_content)
                     meta_desc = clean[:155] + "..."

                post = wp.create_post(
                    title=final_title,
                    content=final_content,
                    featured_media_id=featured_media_id,
                    status='publish',
                    yoast_keyword=keyword,
                    yoast_meta_desc=meta_desc
                )
                link = post.get('link')
                print(f"     ✅ POSTED SUCCESSFULLY! Link: {link}")

                # Update Sheet
                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")

                # ---------------------------------------------------------
                # STEP 6: GROWTH HACKER (New Topics)
                # ---------------------------------------------------------
                print("     6. Growth Hacker Agent: Suggesting new topics...")
                new_topics = brain.identify_new_topics(final_title, final_content)
                for topic in new_topics:
                    print(f"        💡 New Idea: {topic}")
                    sheets.add_new_topic(site['spreadsheet_id'], topic)

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"     ❌ FAILED process keyword '{keyword}': {e}")
                # Optional: Update sheet with Error status

if __name__ == "__main__":
    main()
