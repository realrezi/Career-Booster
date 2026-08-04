import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Upload, CheckCircle, Sparkles, Key, 
  AlertTriangle, ArrowRight, ArrowLeft, Download, Eye, 
  RotateCcw, ShieldCheck, Cpu, RefreshCw, Target, Mail
} from 'lucide-react';

const API_BASE = '/api';

export default function App() {
  const [showIntro, setShowIntro] = useState(true);
  const [step, setStep] = useState(1);
  const fileInputRef = useRef(null);
  
  // API Keys & Model
  const [geminiKey, setGeminiKey] = useState('');


  // App State
  const [file, setFile] = useState(null);
  const [rawText, setRawText] = useState('');
  const [usedOcr, setUsedOcr] = useState(false);
  const [parsedCv, setParsedCv] = useState(null);
  const [jsonText, setJsonText] = useState('');
  
  const [jobAdText, setJobAdText] = useState('');
  const [fitData, setFitData] = useState(null);
  const [loadingFit, setLoadingFit] = useState(false);
  const [tailoredCv, setTailoredCv] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [error, setError] = useState('');

  // Feature Enhancements: Multi-Theme PDF, DOCX & Cover Letter
  const [selectedTheme, setSelectedTheme] = useState('modern');
  const [coverLetterText, setCoverLetterText] = useState('');
  const [letterType, setLetterType] = useState('academic_phd');
  const [letterTone, setLetterTone] = useState('academic_formal');
  const [letterLength, setLetterLength] = useState('standard');
  const [letterFocus, setLetterFocus] = useState('');
  const [loadingLetter, setLoadingLetter] = useState(false);

  // Remove auto-selection useEffect so user has full control over the model

  // Step 1: Upload PDF & Extract Text
  const handleFileUpload = async (selectedFile) => {
    if (!geminiKey.trim()) {
      setError('A Google Gemini API Key is strictly required to parse your CV. Please enter your Gemini key above.');
      return;
    }
    if (!selectedFile) return;
    // Key is optional now - server engine active!
    setFile(selectedFile);
    setError('');
    setLoading(true);
    setStatusMsg('Extracting PDF text and analyzing structure...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      formData.append('gemini_key', geminiKey.trim().replace(/[\r\n\s]+/g, ''));
      
      const parseRes = await fetch(`${API_BASE}/parse-cv`, {
        method: 'POST',
        body: formData,
      });

      if (!parseRes.ok) {
        let parseErrMsg = 'Parsing failed';
        const pTxt = await parseRes.text();
        try {
          const parseErr = JSON.parse(pTxt);
          parseErrMsg = parseErr.detail || parseErrMsg;
        } catch (_) {
          parseErrMsg = pTxt || parseErrMsg;
        }
        throw new Error(parseErrMsg);
      }

      const parseData = await parseRes.json();
      const cvObj = parseData.parsed_data || parseData.cv_data || parseData;
      setParsedCv(cvObj);
      setJsonText(JSON.stringify(cvObj, null, 2));
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  // Download PDF with Theme
  const handleDownloadPDF = async (themeToUse = selectedTheme) => {
    try {
      const res = await fetch(`${API_BASE}/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cv_data: tailoredCv || parsedCv, theme: themeToUse })
      });
      if (!res.ok) throw new Error('Failed to generate PDF document');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      setPdfUrl(url);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Tailored_CV_${themeToUse}.pdf`;
      a.click();
    } catch (err) {
      setError(err.message);
    }
  };

  // Download DOCX (Word Document)
  const handleDownloadDOCX = async (themeToUse = selectedTheme) => {
    try {
      const res = await fetch(`${API_BASE}/generate-docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cv_data: tailoredCv || parsedCv, theme: themeToUse })
      });
      if (!res.ok) throw new Error('Failed to generate Word document');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Tailored_CV_${themeToUse}.docx`;
      a.click();
    } catch (err) {
      setError(err.message);
    }
  };

  // Generate Cover Letter
  const handleGenerateCoverLetter = async () => {
    if (!jobAdText.trim()) {
      setError('Please provide a job description to generate a cover letter.');
      return;
    }
    setError('');
    setLoadingLetter(true);
    try {
      const res = await fetch(`${API_BASE}/generate-cover-letter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cv_data: tailoredCv || parsedCv,
          job_description: jobAdText,
          letter_type: letterType,
          tone: letterTone,
          length: letterLength,
          custom_focus: letterFocus,
          gemini_key: geminiKey.trim().replace(/[\r\n\s]+/g, ''),
        })
      });
      if (!res.ok) {
        const errObj = await res.json();
        throw new Error(errObj.detail || 'Cover Letter generation failed');
      }
      const data = await res.json();
      setCoverLetterText(data.cover_letter);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingLetter(false);
    }
  };

  // Retry Parse Step
  const handleRetryParse = async () => {
    if (!rawText) return;
    setError('');
    setLoading(true);
    setStatusMsg('Parsing extracted text into Ground Truth CV structure...');
    try {
      const parseRes = await fetch(`${API_BASE}/parse-cv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: rawText,
          gemini_key: geminiKey,
        }),
      });

      if (!parseRes.ok) {
        let parseErrMsg = 'Parsing failed';
        const pTxt = await parseRes.text();
        try {
          const parseErr = JSON.parse(pTxt);
          parseErrMsg = parseErr.detail || parseErrMsg;
        } catch (_) {
          parseErrMsg = pTxt || parseErrMsg;
        }
        throw new Error(parseErrMsg);
      }

      const parseData = await parseRes.json();
      setParsedCv(parseData.cv_data);
      setJsonText(JSON.stringify(parseData.cv_data, null, 2));
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  // Step 2: Handle Manual JSON Edits
  const handleSaveJson = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setParsedCv(parsed);
      setError('');
      setStep(3);
    } catch (err) {
      setError('Invalid JSON syntax. Please verify your edits.');
    }
  };

  // Step 3: Analyze Fit Score
  const handleAnalyzeFit = async () => {
    if (!jobAdText.trim() || !parsedCv) return;
    if (!geminiKey.trim()) {
      setError('A Google Gemini API Key is required to calculate match score. Please enter your key above.');
      return;
    }
    setLoadingFit(true);
    try {
      const res = await fetch(`${API_BASE}/analyze-fit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cv_data: parsedCv,
          job_description: jobAdText,
          gemini_key: geminiKey.trim(),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setFitData(data);
      } else {
        const errTxt = await res.text();
        console.error('Fit score error:', errTxt);
      }
    } catch (err) {
      console.error('Match score analysis error:', err);
    } finally {
      setLoadingFit(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (jobAdText.trim() && parsedCv) {
        handleAnalyzeFit();
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [jobAdText, parsedCv]);

  // Step 4: Tailor CV & Generate PDF
  const handleTailorCV = async () => {
    if (!jobAdText.trim()) {
      setError('Please paste the job advertisement text.');
      return;
    }
    setError('');
    setLoading(true);
    setStatusMsg('Tailoring CV content to match job requirements...');

    try {
      if (!fitData) {
        handleAnalyzeFit();
      }
      const tailorRes = await fetch(`${API_BASE}/tailor-cv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobAdText,
          cv_data: parsedCv,
          gemini_key: geminiKey,
        }),
      });

      if (!tailorRes.ok) {
        const tTxt = await tailorRes.text();
        let tailorErr = { detail: 'Tailoring failed' };
        try { tailorErr = JSON.parse(tTxt); } catch (_) {}
        throw new Error(tailorErr.detail || tTxt || 'Tailoring failed');
      }

      const tailorData = await tailorRes.json();
      setTailoredCv(tailorData.tailored_data);

      // Generate PDF
      setStatusMsg('Generating high-resolution print-ready PDF...');
      const pdfRes = await fetch(`${API_BASE}/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tailorData.tailored_data),
      });

      if (!pdfRes.ok) {
        throw new Error('Failed to generate PDF document');
      }

      const blob = await pdfRes.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setStep(4);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="glass-panel navbar">
        <div className="brand-logo">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>
          <div className="brand-text-container">
            <h1 className="brand-title">Career Booster</h1>
            <p className="brand-subtitle">
              by <a href="https://github.com/realrezi" target="_blank" rel="noreferrer">Ahmadreza Shirdel</a>
            </p>
          </div>
        </div>

        <button 
          className="btn-secondary" 
          style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          onClick={() => setShowIntro(!showIntro)}
        >
          <Sparkles size={15} color="#4f46e5" /> {showIntro ? "Hide Intro" : "Website Guide"}
        </button>
      </header>



      {/* Error Alert */}
      {error && (
        <div className="alert-error animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={20} />
            <div>
              <strong>Error:</strong> {error}
            </div>
          </div>
          {rawText && !parsedCv && step === 1 && (
            <button className="btn-secondary" onClick={handleRetryParse} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
              <RotateCcw size={14} style={{ marginRight: '0.4rem' }}/> Retry Parsing
            </button>
          )}
        </div>
      )}

      {/* Stepper Header */}
      <div className="glass-panel stepper-container">
        <div className={`step-item ${step === 1 ? 'active' : step > 1 ? 'completed' : ''}`} onClick={() => setStep(1)}>
          <div className="step-number">{step > 1 ? <CheckCircle size={18} /> : '1'}</div>
          <span className="step-label">Upload CV</span>
        </div>
        <div className={`step-item ${step === 2 ? 'active' : step > 2 ? 'completed' : ''}`} onClick={() => parsedCv && setStep(2)}>
          <div className="step-number">{step > 2 ? <CheckCircle size={18} /> : '2'}</div>
          <span className="step-label">Verify Ground Truth</span>
        </div>
        <div className={`step-item ${step === 3 ? 'active' : step > 3 ? 'completed' : ''}`} onClick={() => parsedCv && setStep(3)}>
          <div className="step-number">{step > 3 ? <CheckCircle size={18} /> : '3'}</div>
          <span className="step-label">Job & Match Score</span>
        </div>
        <div className={`step-item ${step === 4 ? 'active' : ''}`}>
          <div className="step-number">4</div>
          <span className="step-label">Tailored PDF</span>
        </div>
      </div>

      {/* Main Content Areas */}
      {loading && (
        <div className="glass-panel animate-fade-in" style={{ padding: '3rem', textAlign: 'center', marginBottom: '2rem' }}>
          <RefreshCw size={40} className="spin-icon" style={{ animation: 'spin 1.5s linear infinite', color: '#4f46e5', marginBottom: '1rem' }} />
          <h3>Processing Request...</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>{statusMsg}</p>
        </div>
      )}

      {!loading && (
        <>
          {/* WEBSITE INTRODUCTION & HERO SCREEN */}
      {showIntro && (
        <div className="hero-introduction glass-panel animate-fade-in" style={{ padding: '2.5rem', marginBottom: '2rem', background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)' }}>
          <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 2rem' }}>
            <span style={{ fontSize: '0.82rem', background: '#eef2ff', color: '#4f46e5', padding: '0.35rem 0.85rem', borderRadius: '20px', fontWeight: 700, display: 'inline-block', marginBottom: '0.75rem' }}>
              ✨ AI-Powered Academic & Executive Career Booster
            </span>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
              Transform Your CV & Cover Letter with 100% Truthful AI Precision
            </h2>
            <p style={{ color: '#475569', fontSize: '0.96rem', lineHeight: '1.6' }}>
              Welcome to <strong>Career Booster</strong>! Our platform parses your existing PDF CV into structured data, analyzes your alignment against target job descriptions in real time, tailors your qualifications without inventing fake history, and generates custom motivation letters.
            </p>
          </div>

          {/* 5 Feature Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.25rem' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.25rem', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#e0e7ff', color: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
                <FileText size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>1. Vision PDF Parsing</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: '1.45' }}>
                Extracts degrees, publications, and roles directly from PDF into structured JSON with zero hallucinated credentials.
              </p>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.25rem', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#d1fae5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
                <Target size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>2. Semantic Match Score</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: '1.45' }}>
                Evaluates fit score against target job descriptions and highlights missing domain keywords in real time.
              </p>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.25rem', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#fef3c7', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
                <Sparkles size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>3. 100% Truthful Tailoring</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: '1.45' }}>
                Reframes summaries and reorders achievements for job relevance while preserving 100% of your history with zero omissions.
              </p>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.25rem', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#fae8ff', color: '#c026d3', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
                <Mail size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>4. Cover & Motivation Studio</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: '1.45' }}>
                Generates custom academic motivation letters (Master's, PhD, Postdoc) or corporate cover letters tailored to any job.
              </p>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.25rem', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
                <Download size={20} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>5. PDF & MS Word Exporter</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: '1.45' }}>
                Export ready-to-submit PDFs or editable MS Word (.docx) files in 3 visual themes: Modern, Academic, and Tech.
              </p>
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: '2.25rem' }}>
            <button 
              className="btn-primary" 
              style={{ padding: '0.9rem 2.2rem', fontSize: '1.05rem', fontWeight: 700, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.65rem', boxShadow: '0 10px 25px -4px rgba(99, 102, 241, 0.4)' }}
              onClick={() => setShowIntro(false)}
            >
              Get Started & Enter Studio <ArrowRight size={20} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 1: UPLOAD CV */}
          {step === 1 && (
            <div className="glass-panel animate-fade-in" style={{ padding: '2.5rem' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>📄 Step 1: Upload Your Base Academic CV</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                  Upload your base CV in PDF format. We extract structured sections while strictly avoiding hallucinated credentials.
                </p>
              </div>

                            {/* API Key Configuration Box */}
              <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: 'var(--radius-md)', marginBottom: '2rem', border: '1px solid #cbd5e1' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.1rem', color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Key size={18} /> Required Google Gemini API Key
                  </h3>
                  <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{ fontSize: '0.82rem', background: '#eef2ff', color: '#4f46e5', padding: '0.3rem 0.7rem', borderRadius: '12px', fontWeight: 600, textDecoration: 'none' }}>
                    Get Free Gemini Key ↗
                  </a>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1.25rem', lineHeight: '1.45' }}>
                  A Google Gemini API key is <strong>strictly required</strong> to parse, evaluate, tailor your CV, and generate motivation letters. Your key remains 100% private in browser session memory.
                </p>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    Enter Google Gemini API Key <span style={{ color: 'var(--accent-rose)' }}>*</span>
                  </label>
                  <input 
                    type="password" 
                    className="api-key-input"
                    placeholder="AIzaSy... (Paste your Gemini key here)" 
                    value={geminiKey} 
                    onChange={(e) => {
                      setGeminiKey(e.target.value);
                      if (e.target.value && error.includes('Gemini API Key')) {
                        setError('');
                      }
                    }} 
                  />
                </div>
              </div>

              {/* Native Dropzone & Clickable Label */}
              <input 
                id="cv-pdf-input"
                type="file" 
                accept=".pdf" 
                style={{ display: 'none' }} 
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                    e.target.value = '';
                  }
                }}
              />

              <label 
                htmlFor={geminiKey.trim() ? "cv-pdf-input" : undefined}
                className="dropzone"
                style={{ opacity: !geminiKey.trim() ? 0.75 : 1, cursor: !geminiKey.trim() ? 'pointer' : 'pointer', display: 'block' }}
                onClick={(e) => {
                  if (!geminiKey.trim()) {
                    e.preventDefault();
                    setError('Please enter your Google Gemini API Key above before selecting a file.');
                  }
                }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (!geminiKey.trim()) {
                    setError('Please enter your Google Gemini API Key above before uploading your CV.');
                    return;
                  }
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFileUpload(e.dataTransfer.files[0]);
                  }
                }}
              >
                <div className="dropzone-icon">
                  <Upload size={32} />
                </div>
                <h3>Drag & Drop your PDF file here</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '0.5rem 0 1.25rem' }}>
                  Supports all standard academic and medical PDF layouts
                </p>

                <div 
                  className="btn-primary" 
                  style={{ display: 'inline-flex', pointerEvents: 'none' }}
                >
                  Browse File
                </div>
              </label>
            </div>
          )}

          {/* STEP 2: VERIFY GROUND TRUTH */}
          {step === 2 && (
            <div className="glass-panel animate-fade-in" style={{ padding: '2.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.4rem' }}>📋 Step 2: Verify & Edit Ground Truth JSON</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Review the parsed structure to ensure all degrees, publications, and roles are 100% accurate.
                  </p>
                </div>
                {usedOcr && (
                  <div className="badge-ocr">
                    <AlertTriangle size={14} /> OCR Fallback Used
                  </div>
                )}
              </div>

              <textarea 
                className="custom-textarea" 
                rows={16}
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
                <button className="btn-secondary" onClick={() => setStep(1)}>
                  <ArrowLeft size={16} /> Re-upload PDF
                </button>
                <button className="btn-primary" onClick={handleSaveJson}>
                  Confirm Ground Truth & Next <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: JOB & MATCH SCORE */}
          {step === 3 && (
            <div className="glass-panel animate-fade-in" style={{ padding: '2.5rem' }}>
              <h2 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>📝 Step 3: Target Job Advertisement & Match Score</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Paste the job vacancy text below. Our gap analysis engine evaluates your alignment in real time.
              </p>

              <textarea 
                className="custom-textarea" 
                rows={10}
                placeholder="Paste the job advertisement text here..."
                value={jobAdText}
                onChange={(e) => {
                  setJobAdText(e.target.value);
                  if (fitData) setFitData(null);
                }}
              />

              <div style={{ marginTop: '1rem', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button 
                  className="btn-secondary" 
                  onClick={handleAnalyzeFit} 
                  disabled={!jobAdText.trim() || loadingFit}
                  style={{ padding: '0.6rem 1.2rem', fontSize: '0.88rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  <Cpu size={16} style={{ color: '#4f46e5' }} /> {loadingFit ? 'Calculating Semantic Fit...' : '⚡ Calculate Match Score & Gap Analysis'}
                </button>
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                  {fitData ? '✅ Match score calculated' : 'Click above to evaluate alignment'}
                </span>
              </div>

              {/* Match Score Dashboard */}
              {fitData && (
                <div className="glass-panel" style={{ padding: '1.5rem', margin: '1.5rem 0', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                  <h3 style={{ fontSize: '1.05rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>📊 Fit Score & Gap Analysis</h3>
                  <div className="grid-2" style={{ alignItems: 'center' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div className="score-circle" style={{ '--percentage': `${fitData.fit_percentage * 3.6}deg` }}>
                        <div className="score-circle-inner">
                          <span className="score-value">{fitData.fit_percentage}%</span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Match Score</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Missing Domain Keywords:</h4>
                      {fitData.missing_keywords && fitData.missing_keywords.length > 0 ? (
                        <div>
                          {fitData.missing_keywords.map((kw, i) => (
                            <span key={i} className="badge-missing">{kw}</span>
                          ))}
                        </div>
                      ) : (
                        <p style={{ color: 'var(--accent-emerald)', fontSize: '0.9rem' }}>✅ Excellent alignment! No major keywords missing.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
                <button className="btn-secondary" onClick={() => setStep(2)}>
                  <ArrowLeft size={16} /> Back to Ground Truth
                </button>
                <button className="btn-primary" onClick={handleTailorCV} disabled={!jobAdText.trim()}>
                  <Sparkles size={16} /> Generate Tailored CV <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: TAILORED CV & COVER LETTER HUB */}
          {step === 4 && (
            <div className="glass-panel animate-fade-in" style={{ padding: '2.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>🎉 Step 4: Tailored CV & Cover Letter Studio</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                    Download your tailored CV in PDF or MS Word (.docx), or generate a custom Cover/Motivation Letter below.
                  </p>
                  {fitData && (
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: '#eef2ff', color: '#4f46e5', padding: '0.35rem 0.8rem', borderRadius: '16px', fontSize: '0.84rem', fontWeight: 700 }}>
                      <Target size={16} /> ATS Match Score: {fitData.fit_percentage}% Alignment
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button className="btn-secondary" onClick={() => handleDownloadDOCX(selectedTheme)} style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', borderColor: 'rgba(96, 165, 250, 0.3)', cursor: 'pointer' }}>
                    <Download size={16} /> Export Word (.docx)
                  </button>
                  <button className="btn-primary" onClick={() => handleDownloadPDF(selectedTheme)} style={{ cursor: 'pointer' }}>
                    <Download size={16} /> Download PDF
                  </button>
                </div>
              </div>

              {/* Theme Selector */}
              <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', background: '#f8fafc', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>🎨 Select Visual Theme:</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className={selectedTheme === 'modern' ? 'btn-primary' : 'btn-secondary'} 
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedTheme('modern');
                      handleDownloadPDF('modern');
                    }}
                  >
                    Modern Executive
                  </button>
                  <button 
                    className={selectedTheme === 'academic' ? 'btn-primary' : 'btn-secondary'} 
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedTheme('academic');
                      handleDownloadPDF('academic');
                    }}
                  >
                    Classic Academic
                  </button>
                  <button 
                    className={selectedTheme === 'tech' ? 'btn-primary' : 'btn-secondary'} 
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedTheme('tech');
                      handleDownloadPDF('tech');
                    }}
                  >
                    Minimalist Tech
                  </button>
                </div>
              </div>

              {/* Embedded PDF Viewer */}
              {pdfUrl && (
                <div className="glass-panel" style={{ overflow: 'hidden', height: '550px', border: '1px solid var(--border-color)', marginBottom: '2.5rem' }}>
                  <iframe 
                    src={pdfUrl} 
                    title="Tailored CV Preview" 
                    style={{ width: '100%', height: '100%', border: 'none' }}
                  />
                </div>
              )}

              {/* --- COVER & MOTIVATION LETTER STUDIO --- */}
              <div className="glass-panel" style={{ padding: '2rem', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem', color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      ✉️ Automated Cover & Motivation Letter Studio
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                      Configure custom letter goals, tone, and focus areas to generate an application letter matching your CV to the job.
                    </p>
                  </div>
                  <button 
                    className="btn-primary" 
                    onClick={handleGenerateCoverLetter} 
                    disabled={loadingLetter}
                    style={{ minWidth: '180px', cursor: 'pointer' }}
                  >
                    {loadingLetter ? 'Writing Letter...' : '✨ Generate Letter'}
                  </button>
                </div>

                {/* Options Grid */}
                <div className="grid-2" style={{ marginBottom: '1rem', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '0.3rem', color: 'var(--text-primary)', fontWeight: 600 }}>Letter Goal / Type:</label>
                    <select className="custom-select" value={letterType} onChange={(e) => setLetterType(e.target.value)}>
                      <option value="academic_phd">Academic Motivation Letter (Master's / PhD / Postdoc / Research)</option>
                      <option value="corporate">Corporate Cover Letter (Industry / Enterprise)</option>
                      <option value="executive">Executive Leadership Letter</option>
                      <option value="career_change">Career Transition Letter</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '0.3rem', color: 'var(--text-primary)', fontWeight: 600 }}>Tone & Style:</label>
                    <select className="custom-select" value={letterTone} onChange={(e) => setLetterTone(e.target.value)}>
                      <option value="academic_formal">Formal Scientific & Rigorous</option>
                      <option value="confident_executive">Confident & Results-Driven</option>
                      <option value="passionate">Enthusiastic & Mission-Aligned</option>
                      <option value="direct">Direct & Concise</option>
                    </select>
                  </div>
                </div>

                <div className="grid-2" style={{ marginBottom: '1.25rem', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '0.3rem', color: 'var(--text-primary)', fontWeight: 600 }}>Target Length:</label>
                    <select className="custom-select" value={letterLength} onChange={(e) => setLetterLength(e.target.value)}>
                      <option value="short">Short & Punchy (~300 words)</option>
                      <option value="standard">Standard (~450 words)</option>
                      <option value="comprehensive">Comprehensive (~600 words)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '0.3rem', color: 'var(--text-primary)', fontWeight: 600 }}>Custom Highlights / Key Focus (Optional):</label>
                    <input 
                      type="text" 
                      className="api-key-input"
                      placeholder="e.g. Highlight publications, leadership, or 5+ yrs experience..."
                      value={letterFocus} 
                      onChange={(e) => setLetterFocus(e.target.value)} 
                    />
                  </div>
                </div>

                {/* Generated Letter Display */}
                {coverLetterText && (
                  <div style={{ marginTop: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.85rem', color: '#4f46e5', fontWeight: 600 }}>Generated Letter Output:</span>
                      <button 
                        className="btn-secondary" 
                        style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem', cursor: 'pointer' }}
                        onClick={() => {
                          navigator.clipboard.writeText(coverLetterText);
                          alert('Cover letter copied to clipboard!');
                        }}
                      >
                        📋 Copy Letter Text
                      </button>
                    </div>
                    <textarea 
                      className="custom-textarea" 
                      rows={14} 
                      value={coverLetterText} 
                      onChange={(e) => setCoverLetterText(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
                <button className="btn-secondary" onClick={() => setStep(3)} style={{ cursor: 'pointer' }}>
                  <ArrowLeft size={16} /> Edit Job Ad & Score
                </button>
                <button className="btn-secondary" onClick={() => setStep(1)} style={{ cursor: 'pointer' }}>
                  <RotateCcw size={16} /> Start New CV
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      {/* Educational Use Disclaimer Banner (Positioned at Page Bottom) */}
      <div className="disclaimer-banner animate-fade-in" style={{ marginTop: '3rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <ShieldCheck size={20} color="#4f46e5" />
          <div className="disclaimer-text">
            <strong>Educational & Career Research Notice:</strong> Career Booster is built strictly for educational, demonstration, and career research purposes. API keys and CV files are processed in local session memory and are <strong>never saved</strong> to persistent storage.
          </div>
        </div>
      </div>

      <footer className="app-footer">
        <p>Built with ❤️ by Ahmadreza Shirdel</p>
        <p>
          <a href="mailto:ahmadrezashirdel@gmail.com">ahmadrezashirdel@gmail.com</a> |{' '}
          <a href="https://github.com/realrezi" target="_blank" rel="noreferrer">github.com/realrezi</a>
        </p>
      </footer>
    </div>
  );
}
