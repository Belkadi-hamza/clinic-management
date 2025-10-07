const cities = [
    "Azilal", "Beni Mellal", "Fquih Ben Salah", "Khenifra", "Khouribga",
    "Benslimane", "Berrechid", "Casablanca", "El Jadida", "Mediouna",
    "Mohammedia", "Nouaceur", "Settat", "Sidi Bennour", "Errachidia",
    "Midelt", "Ouarzazate", "Tinghir", "Zagora", "Boulemane",
    "El Hajeb", "Fez", "Ifrane", "Meknes", "Moulay Yacoub",
    "Sefrou", "Taounate", "Taza", "Tahannaout", "Chichaoua",
    "Kalaat Sraghna", "Essaouira", "Marrakesh", "Ben Guerir", "Safi",
    "Youssoufia", "Berkane", "Driouch", "Figuig", "Guercif",
    "Jerada", "Nador", "Oujda", "Taourirt", "Kenitra",
    "Khemisset", "Rabat", "Salé", "Sidi Kacem", "Sidi Slimane",
    "Temara", "Agadir", "Biougra", "Inezgane", "Taroudant",
    "Tata", "Tiznit", "Al Hoceima", "Chefchaouen", "Anjra",
    "Larache", "M'diq", "Ouazzane", "Tangier", "Tétouan",
    "Aousserd", "Dakhla", "Assa", "Guelmim", "Sidi Ifni",
    "Tan-Tan", "Boujdour", "Smara", "Laayoune", "Tarfaya"
];

function populateCities() {
    const citySelect = document.getElementById('city');
    let optionsHTML = '<option value="">Select</option>';
    
    cities.forEach(city => {
        optionsHTML += `<option value="${city}">${city}</option>`;
    });
    
    citySelect.innerHTML = optionsHTML;
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', populateCities);