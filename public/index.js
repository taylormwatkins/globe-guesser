// Import the functions from the SDKs needed
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";
import firebaseConfig from "/firebaseconfig.js";

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// variables for target country and guess counter
let targetCountry = "";
let guessCounter = 7;

// define the API URL
const apiUrl = "https://us-central1-globeguesser-56dad.cloudfunctions.net";


// find the html elements needed
const userMessage = document.getElementById("usermessage");
const tableBody = document.querySelector("#datatable tbody");
const formatter = new Intl.NumberFormat("en-US");
const guessHolder = document.getElementById("guessholder");
const guessForm = document.getElementById("guessform");
const formElements = guessForm.elements;
guessHolder.innerHTML = "Guesses remaining: " + guessCounter;

// make a GET request to fetch data
fetch(apiUrl + "/random_country", {
  method: "GET",
  // mode: 'no-cors',  // Temporary workaround
})
  .then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  })
  .then((data) => {
    console.log("Country data:", data);
    targetCountry = data.name;
  })
  .catch((error) => {
    console.error("There was a problem with the fetch operation:", error);
  });

// make a POST request to check if guess is correct
export function submitGuess(userInput) {
  fetch(apiUrl + "/check_guess", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      guess: userInput,
      target: targetCountry,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      guessForm.reset();
      if (!data.found) {
        // display message if country isn't found
        userMessage.innerHTML = data.message;
      } else if (data.correct) {
        // display message if guess is correct and disable the guess form
        userMessage.innerHTML = data.message;
        for (var i = 0, len = formElements.length; i < len; ++i) {
          formElements[i].disabled = true;
        }
      } else {
        // otherwise, show the comparison data
        userMessage.innerHTML = "";
        addGuess(data);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  function addGuess(guess) {
    // make sure guess isn't a duplicate
    // loop through each row in the table
    // access the cell in the name column and compare
    const nameIndex = 0;
    for (let i = 0; i < tableBody.rows.length; i++) {
      const cell = tableBody.rows[i].cells[nameIndex];
      if (cell.textContent == guess.name) {
        userMessage.innerHTML =
          "Already guessed " + guess.name + ", guess again";
        return;
      }
    }

    // decrement and display guess counter
    guessCounter--;
    guessHolder.innerHTML = "Guesses remaining: " + guessCounter;

    // make a new table row
    const row = document.createElement("tr");

    // create and populate cells
    const nameCell = document.createElement("td");
    nameCell.textContent = guess.name;
    row.appendChild(nameCell);

    const co2Cell = document.createElement("td");
    co2Cell.textContent = formatter.format(guess.co2_difference.toFixed(2));
    row.appendChild(co2Cell);

    const climateCell = document.createElement("td");
    climateCell.textContent = formatter.format(guess.climate_difference);
    row.appendChild(climateCell);

    const areaCell = document.createElement("td");
    areaCell.textContent = formatter.format(guess.land_area_difference);
    row.appendChild(areaCell);

    const continentCell = document.createElement("td");
    continentCell.textContent = guess.continent;
    row.appendChild(continentCell);

    const directionCell = document.createElement("td");
    directionCell.textContent = guess.direction;
    row.appendChild(directionCell);

    // add row to table body
    tableBody.insertBefore(row, tableBody.firstChild);

    // if no more guesses
    // display correct country and disable guess form
    if (guessCounter == 0) {
      userMessage.innerHTML = "Oops! The target country was " + targetCountry;
      for (var i = 0, len = formElements.length; i < len; ++i) {
        formElements[i].disabled = true;
      }
    }
  }
}
