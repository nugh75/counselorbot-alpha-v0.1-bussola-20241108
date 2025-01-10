function calculateZTPIScores(responses) {
  // Reverse code items 9, 24, 25, 41, & 56
  const reverseCodeItems = [9, 24, 25, 41, 56];
  const reversedResponses = {...responses};
  
  reverseCodeItems.forEach(item => {
    if (reversedResponses[item]) {
      reversedResponses[item] = 6 - reversedResponses[item]; // 1->5, 2->4, etc.
    }
  });

  // Calculate factor scores
  const pastNegative = [4, 5, 16, 22, 27, 33, 34, 36, 50, 54];
  const presentHedonistic = [1, 8, 12, 17, 19, 23, 26, 28, 31, 32, 42, 44, 46, 48, 55];
  const future = [6, 9, 10, 13, 18, 21, 24, 30, 40, 43, 45, 51, 56];
  const pastPositive = [2, 7, 11, 15, 20, 25, 29, 41, 49];
  const presentFatalistic = [3, 14, 35, 37, 38, 39, 47, 52, 53];

  // Helper function to calculate average score for a factor
  const calculateFactorScore = (items) => {
    const sum = items.reduce((acc, item) => acc + (reversedResponses[item] || 0), 0);
    return sum / items.length;
  };

  // Double-check calculations by doing them twice
  const scores = {
    pastNegative: [
      calculateFactorScore(pastNegative),
      calculateFactorScore(pastNegative)
    ],
    presentHedonistic: [
      calculateFactorScore(presentHedonistic),
      calculateFactorScore(presentHedonistic)
    ],
    future: [
      calculateFactorScore(future),
      calculateFactorScore(future)
    ],
    pastPositive: [
      calculateFactorScore(pastPositive),
      calculateFactorScore(pastPositive)
    ],
    presentFatalistic: [
      calculateFactorScore(presentFatalistic),
      calculateFactorScore(presentFatalistic)
    ]
  };

  // Verify both calculations match
  const finalScores = {};
  for (const factor in scores) {
    if (Math.abs(scores[factor][0] - scores[factor][1]) > 0.0001) {
      console.log(`Warning: Inconsistency in ${factor} calculations`);
    }
    finalScores[factor] = scores[factor][0];
  }

  return finalScores;
}

// Helper function to validate responses
function validateResponses(responses) {
  const missingItems = [];
  const invalidValues = [];
  
  for (let i = 1; i <= 56; i++) {
    if (!responses[i]) {
      missingItems.push(i);
    } else if (responses[i] < 1 || responses[i] > 5) {
      invalidValues.push(i);
    }
  }
  
  return { missingItems, invalidValues };
}

// ZTPI Questions (Italian version)
const ztpiQuestions = [
  "1. Credo che il modo migliore per godersi la vita sia vivere giorno per giorno.",
  "2. La familiarità delle abitudini quotidiane è confortante per me.",
  "3. Il destino ha un ruolo importante nella mia vita.",
  // ... (add all 56 questions)
  "56. Preferisco fare le cose all'ultimo minuto."
];

// Function to display ZTPI questions
function displayZTPIQuestions() {
  const formContainer = document.getElementById('ztpi-form');
  formContainer.innerHTML = '';

  ztpiQuestions.forEach((question, index) => {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'ztpi-question';
    
    const questionText = document.createElement('p');
    questionText.textContent = question;
    
    const optionsDiv = document.createElement('div');
    optionsDiv.className = 'ztpi-options';
    
    for (let i = 1; i <= 5; i++) {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `question-${index + 1}`;
      input.value = i;
      input.required = true;
      
      label.appendChild(input);
      label.appendChild(document.createTextNode(i));
      optionsDiv.appendChild(label);
    }
    
    questionDiv.appendChild(questionText);
    questionDiv.appendChild(optionsDiv);
    formContainer.appendChild(questionDiv);
  });
}

// Function to collect responses
function collectResponses() {
  const responses = {};
  
  ztpiQuestions.forEach((_, index) => {
    const selected = document.querySelector(`input[name="question-${index + 1}"]:checked`);
    if (selected) {
      responses[index + 1] = parseInt(selected.value);
    }
  });
  
  return responses;
}

// Function to handle ZTPI submission
function handleZTPISubmission() {
  const responses = collectResponses();
  const validation = validateResponses(responses);
  
  if (validation.missingItems.length > 0) {
    alert(`Per favore rispondi a tutte le domande. Mancano le risposte per: ${validation.missingItems.join(', ')}`);
    return;
  }
  
  if (validation.invalidValues.length > 0) {
    alert(`Alcune risposte non sono valide. Per favore controlla: ${validation.invalidValues.join(', ')}`);
    return;
  }
  
  const scores = calculateZTPIScores(responses);
  displayResults(scores);
}

// Function to display results
function displayResults(scores) {
  const resultsDiv = document.createElement('div');
  resultsDiv.className = 'ztpi-results';
  
  const resultText = document.createElement('p');
  resultText.textContent = 'I tuoi punteggi ZTPI:';
  resultsDiv.appendChild(resultText);
  
  for (const [factor, score] of Object.entries(scores)) {
    const factorDiv = document.createElement('div');
    factorDiv.className = 'ztpi-factor';
    
    const factorName = document.createElement('span');
    factorName.textContent = factor + ': ';
    factorName.className = 'factor-name';
    
    const factorScore = document.createElement('span');
    factorScore.textContent = score.toFixed(2);
    factorScore.className = 'factor-score';
    
    factorDiv.appendChild(factorName);
    factorDiv.appendChild(factorScore);
    resultsDiv.appendChild(factorDiv);
  }
  
  const messagesContainer = document.getElementById('chat-messages');
  messagesContainer.appendChild(resultsDiv);
  resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// Initialize ZTPI functionality
document.getElementById('submit-ztpi')?.addEventListener('click', handleZTPISubmission);

// Export functions for use in other modules
export { 
  calculateZTPIScores, 
  validateResponses, 
  displayZTPIQuestions, 
  collectResponses,
  handleZTPISubmission,
  displayResults
};
