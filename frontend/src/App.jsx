import { useEffect, useRef, useState } from 'react'
import './App.css'

const defaultDetection = {
  tier: 3,
  object: 'open pathway',
  hazard: false,
  direction: 'none',
  distance: 'unknown',
  message: '',
  source: 'demo',
}

const demoFallbacks = [
  {
    tier: 1,
    object: 'stairs',
    hazard: true,
    direction: 'center',
    distance: '2 meters',
    message: 'Stop — stairs ahead.',
    source: 'demo',
  },
  {
    tier: 2,
    object: 'obstacle',
    hazard: true,
    direction: 'left',
    distance: '3 meters',
    message: 'Obstacle detected — left.',
    source: 'demo',
  },
  {
    tier: 3,
    object: 'sofa',
    hazard: false,
    direction: 'right',
    distance: 'near',
    message: 'Sofa ahead.',
    source: 'demo',
  },
  {
    tier: 3,
    object: 'open pathway',
    hazard: false,
    direction: 'none',
    distance: 'unknown',
    message: '',
    source: 'demo',
  },
]

const quickPrompts = [
  'What do you see?',
  "What's next?",
  "Where's my class?",
  'Is there a bench nearby?',
]

function speak(text) {
  if (!text || !('speechSynthesis' in window)) {
    return
  }

  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = 0.95
  utterance.pitch = 1.15
  utterance.volume = 1
  window.speechSynthesis.speak(utterance)
}

function formatDirection(direction) {
  const value = String(direction || 'center').toLowerCase()
  if (value === 'left') return 'Left'
  if (value === 'right') return 'Right'
  if (value === 'none') return 'None'
  return 'Center'
}

function App() {
  const videoRef = useRef(null)
  const recognitionRef = useRef(null)
  const inFlightRef = useRef(false)
  const lastSpeechRef = useRef(0)

  const [cameraStatus, setCameraStatus] = useState('Awaiting camera')
  const [detectionStatus, setDetectionStatus] = useState('Ready')
  const [detectionMode, setDetectionMode] = useState('Checking live AI…')
  const [isDetectionActive, setIsDetectionActive] = useState(false)
  const [liveModeAvailable, setLiveModeAvailable] = useState(false)
  const [navigationActive, setNavigationActive] = useState(true)
  const [visionResult, setVisionResult] = useState(defaultDetection)
  const [today, setToday] = useState({
    date: 'Today',
    schedule: [
      { time: '10:00 AM', title: 'CSE 120', location: 'Engineering 2' },
      { time: '12:30 PM', title: 'Lunch', location: 'Cowell Dining Commons' },
      { time: '3:00 PM', title: 'ACM Meeting', location: 'Jack Baskin Engineering' },
    ],
    tasks: ['Submit CSE 120 Homework', 'Reply to project team', 'Review lecture notes'],
    next_class: { time: '10:00 AM', title: 'CSE 120', location: 'Engineering 2' },
  })
  const [question, setQuestion] = useState('What is my next class?')
  const [answer, setAnswer] = useState('Your next class is CSE 120 in Engineering 2.')
  const [navigation, setNavigation] = useState({
    destination: 'Engineering 2',
    direction: 'Center',
    instruction: 'Continue toward the next marked path.',
  })

  const applyVisionResult = (result, speakAllowed = true) => {
    const normalized = {
      tier: Number(result?.tier ?? 3),
      object: String(result?.object || 'scene').toLowerCase(),
      hazard: Boolean(result?.hazard),
      direction: String(result?.direction || 'center').toLowerCase(),
      distance: String(result?.distance || 'unknown'),
      message: String(result?.message || ''),
      source: String(result?.source || 'live'),
    }

    setVisionResult(normalized)
    if (normalized.source === 'demo') {
      setDetectionMode('Demo Mode')
      setDetectionStatus('Demo Mode active')
    } else if (normalized.source === 'live_error') {
      setDetectionMode('LIVE AI ERROR')
      setDetectionStatus('Live AI unavailable')
    } else if (normalized.source === 'idle') {
      setDetectionMode('IDLE')
      setDetectionStatus('System idle')
    } else {
      setDetectionMode('LIVE AI')
      setDetectionStatus('LIVE AI active')
    }

    if (normalized.hazard && normalized.message && speakAllowed) {
      const now = Date.now()
      if (now - lastSpeechRef.current > 7000) {
        lastSpeechRef.current = now
        speak(normalized.message)
      }
    }

    if (normalized.tier === 1) {
      setNavigation({
        destination: 'Engineering 2',
        direction: formatDirection(normalized.direction),
        instruction: 'Stop and use the safer route ahead.',
      })
      return
    }

    if (normalized.tier === 2) {
      setNavigation({
        destination: 'Engineering 2',
        direction: formatDirection(normalized.direction),
        instruction: normalized.message || 'Continue with caution toward the open path.',
      })
      return
    }

    setNavigation({
      destination: 'Engineering 2',
      direction: 'Center',
      instruction: normalized.object === 'open pathway' ? 'Open path ahead. Continue steadily.' : 'No immediate hazard detected.',
    })
  }

  const captureAndAnalyzeFrame = async () => {
    if (!isDetectionActive || inFlightRef.current) {
      return
    }

    const video = videoRef.current
    if (!video || video.readyState < 2) {
      return
    }

    inFlightRef.current = true
    setDetectionStatus('Analyzing frame…')

    try {
      const canvas = document.createElement('canvas')
      const width = video.videoWidth || 1280
      const height = video.videoHeight || 720
      canvas.width = width
      canvas.height = height
      const context = canvas.getContext('2d')
      context.drawImage(video, 0, 0, width, height)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.82)
      const imageData = dataUrl.split(',')[1]

      const response = await fetch('/api/vision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData }),
      })

      const data = await response.json()
      applyVisionResult(data, true)
    } catch (error) {
      applyVisionResult({
        tier: 3,
        object: 'scene',
        hazard: false,
        direction: 'none',
        distance: 'unknown',
        message: 'Live Gemma unavailable. Please verify API credentials and model access.',
        source: 'live_error',
      }, false)
    } finally {
      inFlightRef.current = false
    }
  }

  useEffect(() => {
    async function loadToday() {
      try {
        const response = await fetch('/api/today')
        const data = await response.json()
        setToday(data)
      } catch (error) {
        console.error('Failed to load daily companion data', error)
      }
    }

    async function loadSystemStatus() {
      try {
        const response = await fetch('/api/system')
        const data = await response.json()
        setLiveModeAvailable(!Boolean(data?.demo_mode))
        if (data?.demo_mode) {
          setDetectionMode('Demo Mode')
          setDetectionStatus('Demo Mode active')
        } else {
          setDetectionMode('LIVE AI')
          setDetectionStatus('LIVE AI active')
        }
      } catch (error) {
        console.error('Failed to load system status', error)
      }
    }

    loadToday()
    loadSystemStatus()
  }, [])

  useEffect(() => {
    async function startCamera() {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraStatus('Camera unavailable')
        return
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false,
        })

        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
        setCameraStatus('Camera live')
      } catch (error) {
        setCameraStatus('Camera permission denied')
      }
    }

    startCamera()

    return () => {
      const video = videoRef.current
      if (video && video.srcObject) {
        video.srcObject.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setQuestion(transcript)
      handleAsk(transcript)
    }

    recognition.onerror = () => {
      setDetectionStatus('Voice input unavailable')
    }

    recognitionRef.current = recognition
  }, [])

  useEffect(() => {
    if (!isDetectionActive) {
      setDetectionStatus('Paused')
      return
    }

    setDetectionStatus(liveModeAvailable ? 'LIVE AI active' : 'Demo Mode active')
    captureAndAnalyzeFrame()
    const interval = setInterval(() => {
      captureAndAnalyzeFrame()
    }, 2800)

    return () => clearInterval(interval)
  }, [isDetectionActive, liveModeAvailable])

  async function handleAsk(nextQuestion = question) {
    const trimmed = (nextQuestion || '').trim()
    const baseQuestion = trimmed || 'What is around me?'
    setQuestion(baseQuestion)

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: baseQuestion, context: visionResult }),
      })

      const data = await response.json()
      setAnswer(data.answer)
      if (data.answer) {
        speak(data.answer)
      }
    } catch (error) {
      const fallback =
        baseQuestion.toLowerCase().includes('next class') || baseQuestion.toLowerCase().includes('where\'s my class')
          ? 'Your next class is CSE 120 in Engineering 2.'
          : baseQuestion.toLowerCase().includes('today') || baseQuestion.toLowerCase().includes('schedule')
            ? 'Today you have CSE 120, lunch, and ACM Meeting.'
            : baseQuestion.toLowerCase().includes('task')
              ? 'Your tasks are to submit CSE 120 Homework, reply to your project team, and review lecture notes.'
              : 'I see an open pathway with no immediate hazards.'

      setAnswer(fallback)
      speak(fallback)
    }
  }

  function startDetection() {
    setIsDetectionActive(true)
    if (!liveModeAvailable) {
      setDetectionMode('Demo Mode')
      setDetectionStatus('Demo Mode active')
      speak('Demo Mode active.')
    } else {
      setDetectionMode('LIVE AI')
      setDetectionStatus('LIVE AI active')
      speak('SlugGuide active.')
    }
    setNavigation({
      destination: 'Engineering 2',
      direction: 'Center',
      instruction: 'Proceed carefully to the next marked path.',
    })
  }

  function stopDetection() {
    setIsDetectionActive(false)
    setDetectionMode('PAUSED')
    setDetectionStatus('Paused')
    setVisionResult({
      ...defaultDetection,
      source: 'idle',
      message: 'System idle.',
    })
    setNavigation({
      destination: 'Engineering 2',
      direction: 'Center',
      instruction: 'Monitoring paused.',
    })
  }

  function runDemoMode() {
    if (liveModeAvailable) {
      setDetectionStatus('Live AI enabled; demo mode is unavailable.')
      setDetectionMode('LIVE AI')
      return
    }

    const sample = demoFallbacks[0]
    applyVisionResult(sample, true)
    setDetectionMode('Demo Mode')
    setDetectionStatus('Demo Mode active')
    speak('Demo Mode active.')
  }

  function handleVoiceInput() {
    if (recognitionRef.current) {
      recognitionRef.current.start()
      setDetectionStatus('Listening…')
      return
    }

    setDetectionStatus('Voice not supported')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Accessibility AI companion</p>
          <h1>SlugGuide</h1>
        </div>
        <div className="tagline">Navigate the world. Navigate your day.</div>
      </header>

      <main className="app-grid">
        <section className="panel vision-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Live scene</p>
              <h2>Understanding your surroundings</h2>
            </div>
            <span className={`status-pill ${detectionMode === 'LIVE AI' ? 'live' : 'demo'}`}>
              {detectionMode}
            </span>
          </div>

          <div className="camera-wrap">
            <video ref={videoRef} autoPlay playsInline muted />
            <div className="camera-overlay" aria-hidden="true" />
            <div className="camera-badge">{cameraStatus}</div>
          </div>

          <div className="vision-summary">
            <span className="summary-label">{visionResult.tier === 1 ? 'STOP' : visionResult.tier === 2 ? 'GUIDE' : 'ALL CLEAR'}</span>
            <h3>{visionResult.hazard ? String(visionResult.object).toUpperCase() : String(visionResult.object || 'PATH').toUpperCase()}</h3>
            <p>{visionResult.message || 'No immediate hazards detected.'}</p>
            <div className="meta-row">
              <span>{formatDirection(visionResult.direction)}</span>
              <span>{visionResult.distance}</span>
            </div>
          </div>

          <div className="controls-row">
            <button type="button" className="primary" onClick={startDetection}>Start AI detection</button>
            <button type="button" className="secondary" onClick={stopDetection}>Stop</button>
            <button type="button" className="demo" onClick={runDemoMode} disabled={liveModeAvailable}>Demo Mode</button>
          </div>

          <div className="status-row">
            <span>Detection status</span>
            <strong>{detectionStatus}</strong>
          </div>
        </section>

        <aside className="panel companion-panel">
          <div className="day-hero">
            <p className="eyebrow">Your day</p>
            <h2>Good morning</h2>
            <p>Here&apos;s what&apos;s ahead.</p>
          </div>

          <div className="next-card">
            <span className="mini-label">Next</span>
            <h3>{today.next_class?.title || 'CSE 120'}</h3>
            <p>{today.next_class?.time || '10:00 AM'}</p>
            <small>{today.next_class?.location || 'Engineering 2'}</small>
          </div>

          <div className="tasks-card">
            <div className="tasks-header">
              <span className="mini-label">Tasks</span>
              <strong>{(today.tasks || []).length} tasks remaining</strong>
            </div>
            <ul>
              {(today.tasks || []).map((task) => <li key={task}>{task}</li>)}
            </ul>
          </div>

          <div className="schedule-card">
            <div className="tasks-header">
              <span className="mini-label">Schedule</span>
              <strong>{today.date || 'Today'}</strong>
            </div>
            <ul>
              {(today.schedule || []).map((entry) => (
                <li key={`${entry.time}-${entry.title}`}>
                  <span>{entry.time}</span>
                  <div>
                    <strong>{entry.title}</strong>
                    <small>{entry.location}</small>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <section className="panel navigation-panel">
          <div className="panel-header compact">
            <div>
              <p className="eyebrow">Navigation</p>
              <h2>{navigation.destination}</h2>
            </div>
            <button type="button" className="ghost" onClick={() => setNavigationActive((active) => !active)}>
              {navigationActive ? 'Navigation active' : 'Navigation off'}
            </button>
          </div>

          <div className="route-card">
            <div className="route-metric">
              <span>Distance</span>
              <strong>120 m</strong>
            </div>
            <div className="route-metric">
              <span>Next</span>
              <strong>{navigation.direction}</strong>
            </div>
          </div>

          <div className="instruction-box">
            <span className="mini-label">Current instruction</span>
            <strong>{navigation.instruction}</strong>
          </div>

          <div className="controls-row small-gap">
            <button type="button" className="primary" onClick={() => setNavigationActive(true)}>Start navigation</button>
            <button type="button" className="secondary" onClick={() => setNavigationActive(false)}>Stop</button>
          </div>
        </section>

        <aside className="panel alert-panel">
          <div className="panel-header compact">
            <div>
              <p className="eyebrow">Alert</p>
              <h2>Current signal</h2>
            </div>
          </div>

          <div className={`alert-card ${visionResult.tier === 1 ? 'tier-alert' : visionResult.tier === 2 ? 'tier-guide' : 'tier-silence'}`}>
            <span className="alert-badge">{visionResult.tier === 1 ? 'ALERT' : visionResult.tier === 2 ? 'GUIDE' : 'SILENCE'}</span>
            <h3>{String(visionResult.object || 'scene').toUpperCase()}</h3>
            <p>{visionResult.message || 'No immediate hazard.'}</p>
            <div className="meta-row">
              <span>{formatDirection(visionResult.direction)}</span>
              <span>{visionResult.distance}</span>
            </div>
          </div>
        </aside>

        <section className="panel assistant-panel">
          <div className="panel-header compact">
            <div>
              <p className="eyebrow">Ask SlugGuide</p>
              <h2>Anything you need</h2>
            </div>
          </div>

          <div className="prompt-chips" aria-label="Suggested prompts">
            {quickPrompts.map((prompt) => (
              <button key={prompt} type="button" className="chip" onClick={() => setQuestion(prompt)}>
                {prompt}
              </button>
            ))}
          </div>

          <div className="ask-box">
            <textarea
              aria-label="Ask SlugGuide"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={3}
              placeholder="Ask SlugGuide anything..."
            />
            <div className="ask-actions">
              <button type="button" className="primary" onClick={() => handleAsk()}>Ask</button>
              <button type="button" className="secondary" onClick={handleVoiceInput}>🎙 Talk</button>
            </div>
          </div>

          <div className="answer-box">
            <strong>SlugGuide response</strong>
            <p>{answer}</p>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
