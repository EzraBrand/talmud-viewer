// Updated to use native fetch instead of node-fetch
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const { input_method, tractate, page, section, url } = req.body;
    
    // Handle URL parsing or direct reference
    let reference;
    
    if (input_method === 'url') {
      // Parse the Sefaria URL to extract reference
      const urlParts = new URL(url).pathname.split('/');
      const refPart = urlParts[urlParts.length - 1];
      const match = refPart.match(/([^\.]+)\.([^\.]+)(?:\.([^\.]+))?/);
      
      if (!match) {
        return res.status(400).json({ error: 'Invalid URL format' });
      }
      
      reference = {
        tractate: match[1],
        page: match[2],
        section: match[3] ? parseInt(match[3]) : null
      };
    } else {
      // Direct reference from dropdowns
      reference = {
        tractate,
        page,
        section: section ? parseInt(section) : null
      };
    }
    
    // Construct the API URL
    const baseUrl = "https://www.sefaria.org/api/texts/";
    const apiRef = `${reference.tractate}.${reference.page}`;
    
    // Make request to Sefaria API
    let apiResponse = await fetch(`${baseUrl}${encodeURIComponent(apiRef)}`);
    
    // Try with "Bavli" prefix if the direct reference fails
    if (!apiResponse.ok) {
      apiResponse = await fetch(`${baseUrl}${encodeURIComponent('Bavli ' + apiRef)}`);
      
      if (!apiResponse.ok) {
        return res.status(404).json({ error: 'Text not found' });
      }
    }
    
    const data = await apiResponse.json();
    
    // Process the response
    const result = {
      span: `${reference.tractate} ${reference.page}${reference.section ? ':' + reference.section : ''}`,
      sections: []
    };
    
    // Filter to specific section if requested
    const heText = data.he || [];
    const enText = data.text || [];
    
    if (reference.section !== null) {
      const sectionIdx = reference.section - 1;
      if (sectionIdx >= 0 && sectionIdx < heText.length && sectionIdx < enText.length) {
        result.sections.push({
          hebrew: splitIntoSentences(heText[sectionIdx]),
          english: splitIntoSentences(enText[sectionIdx])
        });
      }
    } else {
      // Process all sections (limit to 20 for performance)
      const limit = Math.min(heText.length, enText.length, 20);
      for (let i = 0; i < limit; i++) {
        result.sections.push({
          hebrew: splitIntoSentences(heText[i]),
          english: splitIntoSentences(enText[i])
        });
      }
    }
    
    // Return the processed data
    return res.status(200).json(result);
    
  } catch (error) {
    console.error('Error processing request:', error);
    return res.status(500).json({ error: 'An error occurred while fetching the text' });
  }
}

// Helper function to split text into sentences
function splitIntoSentences(text) {
  if (!text) return [];
  
  // Simple sentence splitting by punctuation
  return text.split(/(?<=[.!?])\s+/)
    .filter(s => s.trim().length > 0)
    .map(s => s.trim());
}
