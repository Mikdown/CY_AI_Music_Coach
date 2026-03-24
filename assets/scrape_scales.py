"""
Consolidated Web Scraper for Guitar Scales from Berklee Pulse
Each scale type can be scraped individually or all at once
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

# Base URL for all scale data
BASE_URL = "https://pulse.berklee.edu/scales/index.html"


def fetch_scales(section_name, filename):
    """
    Generic function to scrape scales from a specific section.
    
    Args:
        section_name: The heading text to find (e.g., "Major Scales")
        filename: Output CSV filename (e.g., "major_scales.csv")
    
    Returns:
        DataFrame with scale data
    """
    try:
        # Fetch the main webpage
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        scales = []
        
        # Find the h2 header with the section name
        h2_tag = soup.find('h2', string=section_name)
        
        if not h2_tag:
            print(f"❌ Section '{section_name}' not found")
            return None
        
        # Get all links starting from the h2
        all_links = h2_tag.find_all_next('a')
        
        for link in all_links:
            # Stop if we encounter another h2 (next major section)
            next_h2 = link.find_previous('h2')
            if next_h2 and next_h2 != h2_tag:
                break
            
            scale_name = link.get_text(strip=True)
            scale_url = link.get('href')
            
            # Initialize notes and signature
            notes = ""
            signature = ""
            
            try:
                # Fetch the individual scale page
                scale_response = requests.get(scale_url, timeout=5)
                scale_soup = BeautifulSoup(scale_response.content, 'html.parser')
                
                # Find the scales-description div
                scales_desc = scale_soup.find('div', class_='scales-description')
                
                if scales_desc:
                    # Get all strong tags
                    strong_tags = scales_desc.find_all('strong')
                    
                    # First strong tag contains notes
                    if len(strong_tags) > 0:
                        notes = strong_tags[0].get_text(strip=True)
                    
                    # Second strong tag contains signature
                    if len(strong_tags) > 1:
                        signature = strong_tags[1].get_text(strip=True)
                
                # Add a small delay to be respectful to the server
                time.sleep(0.3)
                
            except Exception as e:
                print(f"⚠️  Error fetching {scale_url}: {e}")
            
            scales.append({
                'scale_name': scale_name,
                'url': scale_url,
                'notes': notes,
                'signature': signature
            })
        
        # Create dataframe
        df = pd.DataFrame(scales)
        
        # Save to CSV in home directory
        csv_path = os.path.expanduser(f'~/{filename}')
        df.to_csv(csv_path, index=False)
        
        print(f"✅ Found {len(df)} {section_name} - Saved to {csv_path}")
        return df
        
    except Exception as e:
        print(f"❌ Error scraping {section_name}: {e}")
        return None


# Individual scraper functions for each scale type

def scrape_major_scales():
    """Scrape Major Scales from Berklee Pulse."""
    return fetch_scales("Major Scales", "major_scales.csv")


def scrape_minor_scales():
    """Scrape Minor Scales from Berklee Pulse."""
    return fetch_scales("Minor Scales", "minor_scales.csv")


def scrape_pentatonic_scales():
    """Scrape Pentatonic Scales from Berklee Pulse."""
    return fetch_scales("Pentatonic Scales", "pentatonic_scales.csv")


def scrape_blues_scales():
    """Scrape Blues Scales from Berklee Pulse."""
    return fetch_scales("Blues Scales", "blues_scales.csv")


def scrape_chromatic_scales():
    """Scrape Chromatic Scales from Berklee Pulse."""
    return fetch_scales("Chromatic Scales", "chromatic_scales.csv")


def scrape_modes():
    """Scrape Modes from Berklee Pulse."""
    return fetch_scales("Modes", "modes.csv")


def scrape_diminished_scales():
    """Scrape Diminished Scales from Berklee Pulse."""
    return fetch_scales("Diminished Scales", "diminished_scales.csv")


def scrape_whole_tone_scales():
    """Scrape Whole Tone Scales from Berklee Pulse."""
    return fetch_scales("Whole Tone Scales", "whole_tone_scales.csv")


def scrape_all_scales():
    """Scrape all scale types."""
    print("\n🎸 Starting to scrape all guitar scales from Berklee Pulse...\n")
    
    results = {
        'major': scrape_major_scales(),
        'minor': scrape_minor_scales(),
        'pentatonic': scrape_pentatonic_scales(),
        'blues': scrape_blues_scales(),
        'chromatic': scrape_chromatic_scales(),
        'modes': scrape_modes(),
        'diminished': scrape_diminished_scales(),
        'whole_tone': scrape_whole_tone_scales(),
    }
    
    print("\n✅ All scales scraped successfully!")
    return results


if __name__ == "__main__":
    # Run scrape_all_scales when executed directly
    scrape_all_scales()
