import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re # NEW: Regular Expressions library for finding emails

# 1. SETUP PAGE
st.set_page_config(page_title="Growth & Security Auditor", page_icon="🛡️")

# 2. THE AUDIT FUNCTION
def audit_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # --- MARKETING & SEO CHECKS ---
    title = soup.title.string if soup.title else "No Title Found"
    
    meta_desc = soup.find("meta", attrs={'name': 'description'})
    description = meta_desc['content'] if meta_desc else "Missing Description!"
    desc_len = len(description)
    desc_warning = " (⚠️ Too Long!)" if desc_len > 160 else " (✅ Good Length)"

    ld_json = soup.find("script", {"type": "application/ld+json"})
    ai_readiness = "Pass" if ld_json else "Fail"

    links = soup.find_all('a', href=True)
    broken_links = []
    for link in links[:10]:
        href = link['href']
        if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        full_url = urljoin(url, href)
        try:
            head_resp = requests.head(full_url, headers=headers, timeout=5)
            if head_resp.status_code == 404:
                broken_links.append(full_url)
        except:
            pass
    broken_links_str = ', '.join(broken_links) if broken_links else 'None'

    # --- NEW: SECURITY & PRIVACY CHECKS ---
    # 1. Check if the final resolved URL is using HTTPS (Encryption)
    is_secure = resp.url.startswith('https://')
    
    # 2. Scan for exposed plain-text emails (Spam/Privacy risk)
    # This regex looks for standard email formats in the visible text
    text_content = soup.get_text()
    found_emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text_content))

    return {
        'URL': url,
        'SEO Title': title,
        'Meta Description': description,
        'Meta Description Length': desc_len,
        'Length Warning': desc_warning,
        'Broken Links': broken_links_str,
        'AI Readiness': ai_readiness,
        'Status Code': resp.status_code,
        'HTTPS Secure': is_secure,
        'Exposed Emails': list(found_emails)
    }

# 3. THE USER INTERFACE
st.title("🛡️ Growth & Security Auditor")
st.markdown("Analyze a website for SEO health, AI-readiness, and basic data privacy.")

target_url = st.text_input("Website URL:", placeholder="https://example.com")

if st.button("Run Full Audit"):
    if target_url:
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        
        with st.spinner('Scanning code for marketing and security gaps...'):
            try:
                data = audit_url(target_url)
                
                # --- UI: MARKETING RESULTS ---
                st.subheader("📈 Marketing & AI Search (AEO)")
                aeo_status = "✅ AI Ready" if data['AI Readiness'] == "Pass" else "⚠️ Missing Schema"
                
                c1, c2 = st.columns(2)
                c1.metric("AEO Status", aeo_status)
                c2.metric("Response Code", data['Status Code'])

                st.write(f"**Title:** {data['SEO Title']}")
                st.info(f"**Meta Description:** {data['Meta Description']}")
                st.write(f"**Count:** {data['Meta Description Length']} characters {data['Length Warning']}")
                
                if data['Broken Links'] != 'None':
                    st.error(f"Broken Links Found: {data['Broken Links']}")
                else:
                    st.success("No broken links found in top 10.")

                st.divider() # Adds a nice visual line

                # --- UI: SECURITY RESULTS ---
                st.subheader("🔒 Data Privacy & Security")
                
                s1, s2 = st.columns(2)
                if data['HTTPS Secure']:
                    s1.success("✅ HTTPS Encryption Active")
                else:
                    s1.error("❌ INSECURE: Missing HTTPS")

                email_count = len(data['Exposed Emails'])
                if email_count > 0:
                    s2.warning(f"⚠️ {email_count} Email(s) Exposed")
                    with st.expander("View Exposed Emails (Privacy Risk)"):
                        st.write("These emails can be easily scraped by spam bots:")
                        for email in data['Exposed Emails']:
                            st.code(email)
                else:
                    s2.success("✅ No plain-text emails exposed")

            except Exception as e:
                st.error(f"Error accessing URL: {e}")
    else:
        st.warning("Please enter a URL first.")