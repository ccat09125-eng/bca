const sidebar=document.getElementById("sidebar");
const overlay=document.getElementById("overlay");
const modal=document.getElementById("uploadModal");
const toast=document.getElementById("toast");
const content=document.querySelector(".content");
const dashboardContent=content.innerHTML;
let examTimer=null;
let examSeconds=3*60*60;

const subjects=[
["SUCA101","Fundamentals of Digital Computers",78],["SFEN11","English I",71],["SFCE11","Communicative English I",66],["SUCA102","PC Software Lab",82],["SUCA103","Mathematics I",63],["SUCA104","Programming in C",74],
["SUCA105","Programming in C Lab",69],["SUCA106","Mathematics II",58],["SFEN12","English II",64],["SFCE12","Communicative English II",61],["SUCA201A","C++ and Data Structures",62],["SUCA202","Microprocessors",54],["SUCA203","Numerical and Statistical Methods",67],["SUCA204","Financial Accounting",72],["SUCA205","C++ Data Structures Lab",60]
];

function showToast(message){toast.textContent=message;toast.classList.add("show");clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>toast.classList.remove("show"),2600)}
function closeModal(){modal.classList.remove("open");overlay.classList.remove("open");sidebar.classList.remove("open")}

function subjectView(){return `<div class="dynamic-view"><div class="view-heading"><div><p>SEMESTER I–III</p><h1>Subjects</h1><p>15 course slots mapped from your syllabus and study sources.</p></div><button class="primary" data-action="upload">+ Upload material</button></div><div class="subject-grid">${subjects.map(([code,name,score])=>`<article class="subject-card"><header><span class="subject-code">${code.replace("SUCA","").replace("SFEN","EN").replace("SFCE","CE")}</span><small>${score}% ready</small></header><h3>${name}</h3><p>${code}</p><div class="mini-progress"><i style="width:${score}%"></i></div><button data-subject="${name}">Open learning hub →</button></article>`).join("")}</div></div>`}

function learningView(name="Fundamentals of Digital Computers"){return `<div class="dynamic-view"><div class="view-heading"><div><p>LEARNING HUB · UNIT 2</p><h1>${name}</h1><p>Notes, flashcards, revision and answer-writing practice.</p></div><button class="primary" data-action="back-subjects">← All subjects</button></div><div class="learning-layout"><article class="practice-card"><div class="tabs"><button class="active" data-learning-tab="notes">Notes</button><button data-learning-tab="flashcards">Flashcards</button><button data-learning-tab="answer">Answer writing</button></div><div id="learningPanel">${learningNotes()}</div></article><aside class="plan-card"><h2>Unit progress</h2><div class="progress-ring"><strong>68%</strong></div><p>4 of 6 topics reviewed</p><button class="wide-button" data-action="continue">Continue revision</button></aside></div></div>`}

function learningNotes(){return `<div class="learning-content"><p class="content-kicker">TOPIC SUMMARY</p><h2>Number systems and complements</h2><p>A positional number system represents values using a base and digit weights. Binary uses powers of 2, octal uses powers of 8, and hexadecimal uses powers of 16.</p><div class="formula-box"><strong>Base conversion</strong><span>Divide by the target base and read remainders from bottom to top.</span></div><h3>Key points</h3><ul><li>1's complement: invert every binary digit.</li><li>2's complement: 1's complement plus 1.</li><li>2's complement is used to represent signed binary integers.</li></ul></div>`}

function flashcardsView(){return `<div class="learning-content"><p class="content-kicker">FLASHCARD 1 OF 5</p><div class="flashcard" id="flashcard"><small>QUESTION</small><h2>What is the 2's complement of 101101?</h2><p class="answer-hidden" id="flashcardAnswer">010011</p></div><div class="flashcard-actions"><button data-action="flip-card">Reveal answer</button><button data-action="next-card">Next card →</button></div></div>`}

function answerView(){return `<div class="learning-content"><p class="content-kicker">10-MARK ANSWER PRACTICE</p><h2>Explain the addition and subtraction of binary numbers using complements.</h2><textarea id="answerText" aria-label="Write your answer" placeholder="Structure your answer with an introduction, method, example and conclusion..."></textarea><div class="answer-actions"><span id="wordCount">0 words</span><button data-action="save-answer">Save answer</button></div></div>`}

function pyqView(){
  const academic = window.BCA_ACADEMIC_DATA || { questions: [] };
  const papers = (window.BCA_PYQ_DATA || []).filter(record => record.status === "ok");
  const items = [
    ["Fundamentals of Digital Computers", "UCC1A · 12 papers"],
    ["Mathematics I", "URC1A · 11 papers"],
    ["English I", "UEB1A · 11 papers"],
    ["Programming in C", "UCC2A · 11 papers"],
    ["Mathematics II", "URC2A · 11 papers"],
    ["English II", "UEB2A · 11 papers"],
    ["C++ and Data Structures", "UCC3C · 10 papers"],
    ["Numerical and Statistical Methods", "UNC3A · 10 papers"]
  ];
  return `<div class="dynamic-view"><div class="view-heading"><div><p>QUESTION PAPERS</p><h1>PYQ Practice</h1><p>${papers.length} extracted papers · ${academic.questions.length} model questions</p></div><button class="primary" data-action="random-practice">Random practice</button></div><div class="practice-layout"><article class="practice-card"><h2>Choose a paper series</h2><div class="question-list">${items.map(([name,meta]) => `<button data-practice="${name}"><span><strong>${name}</strong><small>${meta}</small></span><b>Practice →</b></button>`).join("")}</div></article><aside class="plan-card"><h2>PYQ accuracy</h2><div class="progress-ring"><strong>${localStorage.getItem("bca_accuracy") || "68%"}</strong></div><p>Tracked from saved practice attempts</p></aside></div></div>`;
}

function planView(){return `<div class="dynamic-view"><div class="view-heading"><div><p>PERSONALISED PLAN</p><h1>Study Plan</h1><p>Balanced for the 38-day exam window.</p></div><button class="primary" data-action="adjust-plan">Adjust plan</button></div><div class="practice-layout"><article class="practice-card"><h2>Today · 130 minutes</h2><div class="question-list"><button data-action="continue"><span><strong>Database Normalisation</strong><small>DBMS · 45 minutes</small></span><b>Start →</b></button><button data-action="continue"><span><strong>Binary Trees</strong><small>Data Structures · 35 minutes</small></span><b>Continue →</b></button><button data-action="continue"><span><strong>Karnaugh Maps</strong><small>Digital Computers · 50 minutes</small></span><b>Start →</b></button></div></article><aside class="plan-card"><h2>Weekly progress</h2><div class="progress-ring"><strong>64%</strong></div><p>6 of 9 study blocks completed</p></aside></div></div>`}

function mockView(){return `<div class="dynamic-view"><div class="view-heading"><div><p>REALISTIC PRACTICE</p><h1>Mock Exams</h1><p>3-hour university-style theory practice.</p></div><button class="primary" data-action="start-mock">Start mixed mock</button></div><div class="practice-layout"><article class="exam-list"><h2>Available exams</h2><button data-action="start-mock"><span><strong>Semester III Mixed Mock</strong></span><b>75 marks · 3 hrs →</b></button><button data-action="start-mock"><span><strong>Digital Computers</strong></span><b>75 marks · 3 hrs →</b></button><button data-action="start-mock"><span><strong>Numerical and Statistical Methods</strong></span><b>75 marks · 3 hrs →</b></button></article><aside class="plan-card"><h2>Best score</h2><div class="progress-ring"><strong>72%</strong></div><p>Last attempt: 68%</p></aside></div></div>`}

function progressView(){return `<div class="dynamic-view"><div class="view-heading"><div><p>LEARNING ANALYTICS</p><h1>Progress</h1><p>Exam readiness across all 15 subject slots.</p></div><button class="primary" data-action="export-progress">Export report</button></div><div class="practice-layout"><article class="practice-card"><h2>Semester readiness</h2><div class="question-list"><button><span><strong>Semester I</strong><small>5 subjects · 6 day streak</small></span><b>71%</b></button><button><span><strong>Semester II</strong><small>5 subjects · 4 day streak</small></span><b>64%</b></button><button><span><strong>Semester III</strong><small>5 subjects · 12 day streak</small></span><b>68%</b></button></div></article><aside class="plan-card"><h2>Overall readiness</h2><div class="progress-ring"><strong>68%</strong></div><p>+8% improvement this week</p></aside></div></div>`}

function examModal(){return `<div class="exam-modal" id="examModal" role="dialog" aria-modal="true"><header><div><p>LIVE MOCK EXAM</p><h2>Semester III Mixed Mock</h2></div><div class="timer" id="examTimer">03:00:00</div><button id="closeExam">×</button></header><div class="exam-body"><aside><button class="active">1</button><button>2</button><button>3</button><button>4</button><button>5</button></aside><section><p>PART C · 10 MARKS</p><h2>Explain the process of operator overloading in C++. Illustrate with a suitable example.</h2><textarea placeholder="Write your answer here..."></textarea></section></div><footer><button id="saveProgress">Save & exit</button><button id="submitExam">Submit exam</button></footer></div>`}

function render(view){clearInterval(examTimer);examTimer=null;if(view==="Dashboard"){content.innerHTML=dashboardContent;bindGlobalDashboardEvents();return}const views={Subjects:subjectView(),"Study Plan":planView(),"PYQ Practice":pyqView(),"Mock Exams":mockView(),Progress:progressView()};content.innerHTML=`<div class="dynamic-view">${views[view]}</div>`;bindDynamicEvents()}

function bindDynamicEvents(){
  document.querySelectorAll("[data-subject]").forEach(button => button.addEventListener("click", () => {
    content.innerHTML = learningView(button.dataset.subject);
    bindDynamicEvents();
  }));
  document.querySelectorAll("[data-action='back-subjects']").forEach(button => button.addEventListener("click", () => render("Subjects")));
  document.querySelectorAll("[data-learning-tab]").forEach(tab => tab.addEventListener("click", () => {
    document.querySelectorAll("[data-learning-tab]").forEach(item => item.classList.remove("active"));
    tab.classList.add("active");
    const panel = document.getElementById("learningPanel");
    panel.innerHTML = tab.dataset.learningTab === "flashcards" ? flashcardsView() : tab.dataset.learningTab === "answer" ? answerView() : learningNotes();
    bindDynamicEvents();
  }));
  document.querySelectorAll("[data-practice]").forEach(button => button.addEventListener("click", () => openPractice(button.dataset.practice)));
  document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", handleAction));
  const answer = document.getElementById("answerText");
  if (answer) answer.addEventListener("input", () => {
    const words = answer.value.trim() ? answer.value.trim().split(/\s+/).length : 0;
    document.getElementById("wordCount").textContent = `${words} words`;
  });
}

function handleAction(e){
  const action = e.currentTarget.dataset.action;
  if (action === "upload") openUpload();
  if (action === "random-practice") openPractice("Fundamentals of Digital Computers");
  if (action === "adjust-plan") showToast("Plan preferences opened");
  if (action === "export-progress") showToast("Progress report exported");
  if (action === "continue") showToast("Revision session started");
  if (action === "back-subjects") render("Subjects");
  if (action === "flip-card") {
    document.getElementById("flashcardAnswer")?.classList.remove("answer-hidden");
    showToast("Answer revealed");
  }
  if (action === "next-card") showToast("Loading next flashcard");
  if (action === "save-answer") showToast("Answer saved to your revision history");
  if (action === "start-mock") openExam();
}

function openPractice(subjectName){
  const data = window.BCA_ACADEMIC_DATA || { questions: [] };
  const matching = data.questions.filter(record =>
    record.subject.toLowerCase().includes(subjectName.toLowerCase().split(" ")[0]) ||
    subjectName.toLowerCase().includes(record.subject.toLowerCase().split(" ")[0])
  );
  const pool = matching.length ? matching : data.questions;
  const record = pool[Math.floor(Math.random() * pool.length)];
  if (!record) {
    showToast("No model question is available");
    return;
  }
  content.innerHTML = `<div class="dynamic-view"><div class="view-heading"><div><p>${record.marks}-MARK PYQ PRACTICE</p><h1>${subjectName}</h1><p>Model question with source-labelled answer</p></div><button class="primary" data-action="back-pyq">← PYQ library</button></div><div class="practice-layout"><article class="practice-card"><h2>${record.question}</h2><div class="learning-content"><p class="content-kicker">MODEL ANSWER</p><p>${record.answer}</p><textarea id="practiceAnswer" placeholder="Write your answer before checking the model..."></textarea></div></article><aside class="plan-card"><h2>Question source</h2><div class="progress-ring"><strong>${record.marks}</strong></div><p>${record.subject}</p><button class="wide-button" data-action="save-practice">Save attempt</button></aside></div></div>`;
  bindDynamicEvents();
  document.querySelector("[data-action='back-pyq']")?.addEventListener("click", () => render("PYQ Practice"));
  document.querySelector("[data-action='save-practice']")?.addEventListener("click", () => {
    const attempt = document.getElementById("practiceAnswer")?.value || "";
    localStorage.setItem("bca_practice_" + Date.now(), JSON.stringify({ subject: subjectName, question: record.question, answer: attempt }));
    showToast("Practice attempt saved");
  });
}

function openUpload(){modal.classList.add("open");overlay.classList.add("open")}
function openExam(){document.body.insertAdjacentHTML("beforeend",examModal());examSeconds=3*60*60;const em=document.getElementById("examModal");em.classList.add("open");examTimer=setInterval(()=>{examSeconds--;const h=String(Math.floor(examSeconds/3600)).padStart(2,"0"),m=String(Math.floor(examSeconds%3600/60)).padStart(2,"0"),s=String(examSeconds%60).padStart(2,"0");const el=document.getElementById("examTimer");if(el)el.textContent=`${h}:${m}:${s}`},1000);document.getElementById("closeExam")?.addEventListener("click",closeExam);document.getElementById("saveProgress")?.addEventListener("click",closeExam);document.getElementById("submitExam")?.addEventListener("click",()=>{showToast("Mock submitted · Estimated score: 68%");closeExam()})}
function closeExam(){clearInterval(examTimer);examTimer=null;document.getElementById("examModal")?.remove()}

function bindGlobalDashboardEvents(){document.getElementById("startRevision")?.addEventListener("click",()=>showToast("Revision session started: 35 minutes"));document.getElementById("prepareExam")?.addEventListener("click",()=>showToast("Opening your 38-day preparation plan"));document.querySelectorAll(".weak button").forEach(row=>row.addEventListener("click",()=>showToast("Loading targeted practice questions")))}

document.getElementById("menuButton").addEventListener("click",()=>{sidebar.classList.add("open");overlay.classList.add("open")});
document.querySelectorAll(".nav-item").forEach(item=>item.addEventListener("click",()=>{document.querySelector(".nav-item.active")?.classList.remove("active");item.classList.add("active");render(item.dataset.view);closeModal()}));
document.getElementById("uploadButton").addEventListener("click",openUpload);document.getElementById("modalClose").addEventListener("click",closeModal);overlay.addEventListener("click",closeModal);
document.getElementById("fileInput").addEventListener("change",e=>{if(!e.target.files[0])return;closeModal();showToast(e.target.files[0].name+" is ready for processing")});
document.getElementById("searchInput").addEventListener("keydown",e=>{if(e.key==="Enter"&&e.currentTarget.value.trim())showToast("Searching for “"+e.currentTarget.value.trim()+"”")});
document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();document.getElementById("searchInput").focus()}if(e.key==="Escape")closeModal()});
bindGlobalDashboardEvents();
document.addEventListener("input",e=>{if(e.target.id==="answerText")localStorage.setItem("bca_answer_draft",e.target.value)});
document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;if(b.dataset.action==="save-answer")localStorage.setItem("bca_answer_saved",document.getElementById("answerText")?.value||"");if(b.dataset.action==="export-progress")localStorage.setItem("bca_progress_report",JSON.stringify({exportedAt:new Date().toISOString(),readiness:68,subjects}));if(b.dataset.action==="flip-card")localStorage.setItem("bca_flashcard_reviewed",new Date().toISOString());if(b.id==="submitExam")localStorage.setItem("bca_mock_score","68%");});

const api = {
  async post(path, payload) {
    const response = await fetch(path, {
      method: "POST",
      headers: payload instanceof FormData ? undefined : { "Content-Type": "application/json" },
      body: payload instanceof FormData ? payload : JSON.stringify(payload),
    });
    if (!response.ok) throw new Error((await response.json()).error || "Request failed");
    return response.json();
  },
};

const fileInput = document.getElementById("fileInput");
if (fileInput) fileInput.addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  try {
    closeModal();
    showToast("Processing document...");
    const result = await api.post("/api/upload", form);
    showToast(`${result.name} processed · ${result.characters.toLocaleString()} characters`);
  } catch (error) {
    showToast(error.message);
  }
});

document.addEventListener("click", event => {
  const button = event.target.closest("button");
  if (!button) return;

  if (button.dataset.action === "save-practice") {
    const text = document.getElementById("practiceAnswer")?.value || "";
    const heading = document.querySelector(".practice-card h2")?.textContent || "";
    api.post("/api/practice-attempt", {
      subject: document.querySelector(".view-heading h1")?.textContent || "",
      question: heading,
      answer: text,
      timestamp: new Date().toISOString(),
    }).then(result => showToast(`Practice attempt saved · ${result.attemptCount} total`)).catch(error => showToast(error.message));
  }

  if (button.dataset.action === "save-answer") {
    api.post("/api/answer", {
      subject: document.querySelector(".view-heading h1")?.textContent || "",
      answer: document.getElementById("answerText")?.value || "",
      timestamp: new Date().toISOString(),
    }).catch(error => showToast(error.message));
  }

  if (button.id === "submitExam") {
    api.post("/api/mock", {
      title: "Semester III Mixed Mock",
      score: 68,
      timestamp: new Date().toISOString(),
    }).catch(error => showToast(error.message));
  }

  if (button.dataset.action === "export-progress") {
    fetch("/api/report")
      .then(response => response.json())
      .then(report => {
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "bca-progress-report.json";
        link.click();
        URL.revokeObjectURL(url);
      })
      .catch(error => showToast(error.message));
  }
});
