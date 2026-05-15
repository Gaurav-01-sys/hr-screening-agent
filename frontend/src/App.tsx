import { useState } from 'react'
import axios from 'axios'
import { CheckCircle, XCircle, FileText, Briefcase, RefreshCw, Activity, ArrowRight } from 'lucide-react'

interface RuleResult { rule_id: string; passed: boolean; severity: string; message: string; evidence: any[] }
interface ScoreBreakdown { mandatory_fit: number; experience_depth: number; skill_match: number; final_score: number; [key:string]: number }
interface ScreeningResponse { recommendation: string; hard_fail: boolean; rule_results: RuleResult[]; scores: ScoreBreakdown; explanation: string }

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default function App() {
  const [phase, setPhase] = useState<'INGEST' | 'REVIEW' | 'RESULT'>('INGEST')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [resumeText, setResumeText] = useState('')
  const [jdText, setJdText] = useState('')
  const [ruleNotes, setRuleNotes] = useState('')
  
  const [screeningReq, setScreeningReq] = useState<any>(null)
  const [screeningRes, setScreeningRes] = useState<ScreeningResponse | null>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, setter: React.Dispatch<React.SetStateAction<string>>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await axios.post(`${API_URL}/parse-document`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      if (res.data.error) {
        setError(res.data.error);
      } else {
        setter(res.data.text);
      }
    } catch (err: any) {
      setError(err.message || "Failed to parse document.");
    } finally {
      setIsLoading(false);
      e.target.value = ''; // reset input
    }
  }

  const handleExtract = async () => {
    if (!resumeText || !jdText) {
      setError("Please provide both Resume and Job Description texts.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/extract`, {
        resume_text: resumeText,
        jd_text: jdText,
        mandatory_rule_notes: ruleNotes
      });
      setScreeningReq(res.data);
      setPhase('REVIEW');
    } catch (err: any) {
      setError(err.message || "Failed to extract data. Ensure the backend is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  }

  const handleScreening = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/screen`, screeningReq);
      setScreeningRes(res.data);
      setPhase('RESULT');
    } catch (err: any) {
      setError(err.message || "Failed to screen candidate.");
    } finally {
      setIsLoading(false);
    }
  }

  const renderIngest = () => (
    <div className="animate-fade-in flex-col gap-6">
      <div className="glass-panel w-full">
        <h2 className="flex items-center gap-2"><FileText /> Upload Documents</h2>
        <p>Paste your candidate's resume and the job description below.</p>
        
        <div className="grid grid-cols-2 gap-6 mt-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-secondary font-medium">Resume Text</label>
              <label className="btn text-xs px-2 py-1 bg-slate-800 text-secondary cursor-pointer hover:bg-slate-700 rounded border border-slate-700">
                <input type="file" className="hidden" accept=".pdf,.docx" onChange={(e) => handleFileUpload(e, setResumeText)} />
                Upload PDF/DOCX
              </label>
            </div>
            <textarea 
              rows={8} 
              value={resumeText} 
              onChange={e => setResumeText(e.target.value)}
              placeholder="Paste the raw text of the resume here..."
            />
          </div>
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-secondary font-medium">Job Description Text</label>
              <label className="btn text-xs px-2 py-1 bg-slate-800 text-secondary cursor-pointer hover:bg-slate-700 rounded border border-slate-700">
                <input type="file" className="hidden" accept=".pdf,.docx" onChange={(e) => handleFileUpload(e, setJdText)} />
                Upload PDF/DOCX
              </label>
            </div>
            <textarea 
              rows={8} 
              value={jdText} 
              onChange={e => setJdText(e.target.value)}
              placeholder="Paste the job requirements here..."
            />
          </div>
        </div>
        
        <div className="mt-4">
          <label className="mb-2 block text-secondary font-medium">Mandatory Rule Notes (Optional)</label>
          <textarea 
            rows={3} 
            value={ruleNotes} 
            onChange={e => setRuleNotes(e.target.value)}
            placeholder="E.g., Must have 24 months of React experience."
          />
        </div>
        
        <div className="flex justify-between items-center mt-6">
          {error && <span className="text-error">{error}</span>}
          <button className="btn btn-primary ml-auto" onClick={handleExtract} disabled={isLoading}>
            {isLoading ? <div className="spinner"></div> : <><Activity /> Analyze & Extract</>}
          </button>
        </div>
      </div>
    </div>
  )

  const renderReview = () => {
    if (!screeningReq) return null;
    return (
      <div className="animate-fade-in flex-col gap-6">
        <div className="glass-panel w-full">
          <h2 className="flex items-center gap-2"><Briefcase /> Human-in-the-Loop Review</h2>
          <p>Review the AI-extracted skills and adjust them if necessary before final scoring.</p>
          
          <div className="mt-6">
            <h3>Extracted Skills</h3>
            <table>
              <thead>
                <tr>
                  <th>Skill</th>
                  <th>Months</th>
                  <th>Evidence Snippet</th>
                </tr>
              </thead>
              <tbody>
                {screeningReq.candidate.skills.map((s: any, idx: number) => (
                  <tr key={idx}>
                    <td>
                      <input 
                        value={s.skill} 
                        onChange={e => {
                          const newReq = {...screeningReq};
                          newReq.candidate.skills[idx].skill = e.target.value;
                          setScreeningReq(newReq);
                        }} 
                      />
                    </td>
                    <td>
                      <input 
                        type="number" 
                        value={s.months} 
                        onChange={e => {
                          const newReq = {...screeningReq};
                          newReq.candidate.skills[idx].months = parseInt(e.target.value) || 0;
                          setScreeningReq(newReq);
                        }} 
                      />
                    </td>
                    <td className="text-secondary text-sm">
                      {s.evidence && s.evidence.length > 0 ? s.evidence[0].snippet : "No evidence"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6">
            <h3>Extracted Fields Review</h3>
            <table>
              <thead>
                <tr>
                  <th>Field Name</th>
                  <th>AI Value</th>
                  <th>Human Value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {screeningReq.candidate.fields_for_review?.map((f: any, idx: number) => (
                  <tr key={idx}>
                    <td className="text-secondary font-medium">{f.name.replace(/_/g, " ").toUpperCase()}</td>
                    <td className="text-secondary">{f.ai_value || "-"}</td>
                    <td>
                      <input 
                        value={f.human_value || ''} 
                        onChange={e => {
                          const newReq = {...screeningReq};
                          newReq.candidate.fields_for_review[idx].human_value = e.target.value;
                          if (e.target.value) {
                             newReq.candidate.fields_for_review[idx].review_status = 'corrected';
                          }
                          setScreeningReq(newReq);
                        }} 
                        placeholder="Enter correction..."
                        style={{ padding: '0.25rem 0.5rem' }}
                      />
                    </td>
                    <td>
                      <select 
                        value={f.review_status} 
                        onChange={e => {
                          const newReq = {...screeningReq};
                          newReq.candidate.fields_for_review[idx].review_status = e.target.value;
                          setScreeningReq(newReq);
                        }}
                        style={{ padding: '0.25rem 0.5rem', width: 'auto' }}
                      >
                        <option value="pending">Pending</option>
                        <option value="approved">Approved</option>
                        <option value="rejected">Rejected</option>
                        <option value="corrected">Corrected</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center mt-6">
            <button className="btn" onClick={() => setPhase('INGEST')} style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }}>Back</button>
            <button className="btn btn-primary" onClick={handleScreening} disabled={isLoading}>
              {isLoading ? <div className="spinner"></div> : <><ArrowRight /> Run Scoring Rules</>}
            </button>
          </div>
        </div>
      </div>
    )
  }

  const renderResult = () => {
    if (!screeningRes) return null;
    return (
      <div className="animate-fade-in flex-col gap-6">
        <div className="glass-panel w-full text-center">
          <h1>{screeningRes.recommendation.replace("_", " ").toUpperCase()}</h1>
          <p className="mt-2 text-lg" style={{ color: 'white' }}>{screeningRes.explanation}</p>
          <div className="flex justify-center gap-4 mt-4">
            <div className="badge badge-neutral text-lg p-2 px-4">Score: {screeningRes.scores.final_score.toFixed(1)}</div>
            <div className={`badge ${screeningRes.hard_fail ? 'badge-error' : 'badge-success'} text-lg p-2 px-4`}>
              {screeningRes.hard_fail ? 'Hard Fail: YES' : 'Hard Fail: NO'}
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-6 mt-6">
          <div className="glass-panel">
            <h3>Rule Evaluations</h3>
            <div className="mt-4 flex flex-col gap-4">
              {screeningRes.rule_results.map((rr, i) => (
                <div key={i} className="p-4 rounded-lg" style={{ background: rr.passed ? 'var(--success-bg)' : 'var(--error-bg)', border: `1px solid ${rr.passed ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
                  <div className="flex items-center gap-2 font-medium" style={{ color: rr.passed ? 'var(--success)' : 'var(--error)' }}>
                    {rr.passed ? <CheckCircle size={18} /> : <XCircle size={18} />}
                    {rr.rule_id}
                  </div>
                  <p className="mt-2 text-sm mb-0" style={{ color: 'white' }}>{rr.message}</p>
                </div>
              ))}
            </div>
          </div>
          
          <div className="glass-panel">
            <h3>Score Breakdown</h3>
            <div className="mt-4 flex flex-col gap-4">
              {Object.entries(screeningRes.scores).map(([k, v]) => {
                if (k === 'final_score') return null;
                return (
                  <div key={k}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-secondary">{k.replace(/_/g, " ").toUpperCase()}</span>
                      <span>{Number(v).toFixed(2)}</span>
                    </div>
                    <div className="w-full rounded-full h-2" style={{ background: 'rgba(255,255,255,0.1)' }}>
                      <div className="bg-primary h-2 rounded-full" style={{ width: `${Math.min(100, Number(v) * 100)}%` }}></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="flex justify-center mt-6">
          <button className="btn" onClick={() => { setPhase('INGEST'); setScreeningReq(null); setScreeningRes(null); setResumeText(''); setJdText(''); }} style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }}>
            <RefreshCw size={16} /> Start New Screening
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="mb-8 text-center animate-fade-in">
        <h1 className="mb-2">HR Intelligence Platform</h1>
        <p>Agentic Candidate Screening & Verification</p>
      </div>

      <div className="flex justify-center mb-8 gap-4 text-sm font-medium text-secondary animate-fade-in">
        <div className={`flex items-center gap-2 ${phase === 'INGEST' ? 'text-primary' : ''}`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${phase === 'INGEST' ? 'bg-primary text-white' : 'background: rgba(255,255,255,0.1)'}`} style={{ background: phase === 'INGEST' ? '' : 'rgba(255,255,255,0.1)' }}>1</div> Ingest
        </div>
        <div className="w-8 h-[1px] bg-glass-border my-auto" style={{ background: 'rgba(255,255,255,0.1)' }}></div>
        <div className={`flex items-center gap-2 ${phase === 'REVIEW' ? 'text-primary' : ''}`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${phase === 'REVIEW' ? 'bg-primary text-white' : 'background: rgba(255,255,255,0.1)'}`} style={{ background: phase === 'REVIEW' ? '' : 'rgba(255,255,255,0.1)' }}>2</div> Review
        </div>
        <div className="w-8 h-[1px] bg-glass-border my-auto" style={{ background: 'rgba(255,255,255,0.1)' }}></div>
        <div className={`flex items-center gap-2 ${phase === 'RESULT' ? 'text-primary' : ''}`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${phase === 'RESULT' ? 'bg-primary text-white' : 'background: rgba(255,255,255,0.1)'}`} style={{ background: phase === 'RESULT' ? '' : 'rgba(255,255,255,0.1)' }}>3</div> Result
        </div>
      </div>

      {phase === 'INGEST' && renderIngest()}
      {phase === 'REVIEW' && renderReview()}
      {phase === 'RESULT' && renderResult()}
    </>
  )
}
