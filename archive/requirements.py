import requests
from bs4 import BeautifulSoup
import json

def search_game_by_name(game_name):
    """
    Search for a game by name and return matching results with app IDs.
    
    Args:
        game_name: Name of the game to search for
    
    Returns:
        list: List of matching games with app_id and name
    """
    url = "https://steamcommunity.com/actions/SearchApps/" + game_name
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return []
        
        # Return list of matches (usually returns up to 20 results)
        return [{"app_id": game['appid'], "name": game['name']} for game in results]
        
    except requests.RequestException as e:
        print(f"Search failed: {str(e)}")
        return []
    except json.JSONDecodeError:
        print("Failed to parse search results")
        return []


def get_game_requirements(app_id):
    """
    Get system requirements for a Steam game using the official API.
    
    Args:
        app_id: Steam application ID (string or int)
    
    Returns:
        dict: Game details including requirements
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Check if the request was successful
        if not data[str(app_id)]['success']:
            return {"error": "Game not found or data unavailable"}
        
        game_data = data[str(app_id)]['data']
        
        # Extract relevant information
        result = {
            "name": game_data.get('name', 'Unknown'),
            "app_id": app_id,
            "type": game_data.get('type', 'Unknown'),
            "is_free": game_data.get('is_free', False),
        }
        
        # Get PC requirements
        pc_req = game_data.get('pc_requirements', {})
        if pc_req:
            result['pc_requirements'] = {
                'minimum': pc_req.get('minimum', 'Not specified'),
                'recommended': pc_req.get('recommended', 'Not specified')
            }
        
        # Get Mac requirements if available
        mac_req = game_data.get('mac_requirements', {})
        if mac_req:
            result['mac_requirements'] = {
                'minimum': mac_req.get('minimum', 'Not specified'),
                'recommended': mac_req.get('recommended', 'Not specified')
            }
        
        # Get Linux requirements if available
        linux_req = game_data.get('linux_requirements', {})
        if linux_req:
            result['linux_requirements'] = {
                'minimum': linux_req.get('minimum', 'Not specified'),
                'recommended': linux_req.get('recommended', 'Not specified')
            }
        
        return result
        
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except (KeyError, json.JSONDecodeError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}


def clean_html_requirements(html_text):
    """
    Clean HTML from requirements text to make it more readable.
    
    Args:
        html_text: HTML string containing requirements
    
    Returns:
        str: Clean text without HTML tags
    """
    if not html_text or html_text == 'Not specified':
        return html_text
    
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n', strip=True)


def print_requirements(requirements):
    """Pretty print the requirements."""
    if "error" in requirements:
        print(f"Error: {requirements['error']}")
        return
    
    print(f"\nGame: {requirements['name']}")
    print(f"App ID: {requirements['app_id']}")
    print(f"Type: {requirements['type']}")
    print(f"Free to Play: {requirements['is_free']}")
    print("=" * 60)
    
    # PC Requirements
    if 'pc_requirements' in requirements:
        print("\n🖥️  PC REQUIREMENTS:")
        print("-" * 60)
        
        if requirements['pc_requirements']['minimum'] != 'Not specified':
            print("\nMinimum:")
            print(clean_html_requirements(requirements['pc_requirements']['minimum']))
        
        if requirements['pc_requirements']['recommended'] != 'Not specified':
            print("\nRecommended:")
            print(clean_html_requirements(requirements['pc_requirements']['recommended']))
    
    # Mac Requirements
    if 'mac_requirements' in requirements:
        print("\n🍎 MAC REQUIREMENTS:")
        print("-" * 60)
        
        if requirements['mac_requirements']['minimum'] != 'Not specified':
            print("\nMinimum:")
            print(clean_html_requirements(requirements['mac_requirements']['minimum']))
    
    # Linux Requirements
    if 'linux_requirements' in requirements:
        print("\n🐧 LINUX REQUIREMENTS:")
        print("-" * 60)
        
        if requirements['linux_requirements']['minimum'] != 'Not specified':
            print("\nMinimum:")
            print(clean_html_requirements(requirements['linux_requirements']['minimum']))


# Example usage
if __name__ == "__main__":
    # Search for a game by name
    game_name = "Cyberpunk"
    
    print(f"Searching for '{game_name}'...")
    search_results = search_game_by_name(game_name)
    
    if not search_results:
        print("No games found!")
    else:
        print(f"\nFound {len(search_results)} results:")
        for i, game in enumerate(search_results[:5], 1):  # Show first 5 results
            print(f"{i}. {game['name']} (App ID: {game['app_id']})")
        
        # Get requirements for the first result
        if search_results:
            print(f"\n{'='*60}")
            print(f"Fetching requirements for: {search_results[0]['name']}")
            print('='*60)
            
            requirements = get_game_requirements(search_results[0]['app_id'])
            print_requirements(requirements)
    
    # Alternative: Direct search if you know the exact name
    # app_id = "1091500"  # Cyberpunk 2077
    # requirements = get_game_requirements(app_id)
    # print_requirements(requirements)
