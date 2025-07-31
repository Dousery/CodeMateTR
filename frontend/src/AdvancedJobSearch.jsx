import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdvancedJobSearch.css';

const AdvancedJobSearch = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Dosya türü kontrolü
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
      if (!allowedTypes.includes(file.type)) {
        setError('Lütfen PDF, DOC veya DOCX dosyası seçin.');
        return;
      }
      
      // Dosya boyutu kontrolü (16MB)
      if (file.size > 16 * 1024 * 1024) {
        setError('Dosya boyutu 16MB\'dan küçük olmalıdır.');
        return;
      }
      
      setSelectedFile(file);
      setError('');
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!selectedFile) {
      setError('Lütfen bir CV dosyası seçin.');
      return;
    }

    setIsLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('cv', selectedFile);

    try {
      const response = await fetch('/advanced_cv_job_search', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data);
      } else {
        setError(data.error || 'CV analizi sırasında bir hata oluştu.');
      }
    } catch (err) {
      setError('Sunucu bağlantısında hata oluştu.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatMatchScore = (score) => {
    if (score >= 90) return { text: 'Mükemmel Uyum', color: '#10b981' };
    if (score >= 80) return { text: 'Çok İyi Uyum', color: '#059669' };
    if (score >= 70) return { text: 'İyi Uyum', color: '#0d9488' };
    if (score >= 60) return { text: 'Orta Uyum', color: '#f59e0b' };
    return { text: 'Düşük Uyum', color: '#ef4444' };
  };

  return (
    <div className="advanced-job-search">
      <div className="container">
        <div className="header">
          <h1>🤖 Gelişmiş CV Analizi ve İş Arama</h1>
          <p>
            CrewAI ve LangChain teknolojileri kullanarak CV'nizi analiz eder, 
            en uygun iş alanlarını belirler ve gerçek iş ilanları bulur.
          </p>
        </div>

        {!results && (
          <div className="upload-section">
            <form onSubmit={handleSubmit} className="upload-form">
              <div className="file-upload-area">
                <div className="upload-icon">📄</div>
                <h3>CV Dosyanızı Yükleyin</h3>
                <p>PDF, DOC veya DOCX formatında CV'nizi seçin</p>
                
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="file-input"
                  id="cv-file"
                />
                <label htmlFor="cv-file" className="file-label">
                  {selectedFile ? selectedFile.name : 'Dosya Seç'}
                </label>
              </div>

              {error && <div className="error-message">{error}</div>}

              <button 
                type="submit" 
                className="analyze-btn"
                disabled={isLoading || !selectedFile}
              >
                {isLoading ? (
                  <>
                    <div className="spinner"></div>
                    CV Analiz Ediliyor...
                  </>
                ) : (
                  'CV Analiz Et ve İş Bul'
                )}
              </button>
            </form>
          </div>
        )}

        {results && (
          <div className="results-section">
            <div className="results-header">
              <h2>📊 Analiz Sonuçları</h2>
              <button 
                onClick={() => setResults(null)} 
                className="new-analysis-btn"
              >
                Yeni Analiz
              </button>
            </div>

            {/* CV Analizi */}
            <div className="cv-analysis-section">
              <h3>📋 CV Analizi</h3>
              <div className="analysis-grid">
                <div className="analysis-card">
                  <h4>Beceriler</h4>
                  <div className="skills-list">
                    {results.cv_analysis.skills?.map((skill, index) => (
                      <span key={index} className="skill-tag">{skill}</span>
                    ))}
                  </div>
                </div>
                
                <div className="analysis-card">
                  <h4>Deneyim</h4>
                  <p>{results.cv_analysis.experience_years} yıl</p>
                </div>
                
                <div className="analysis-card">
                  <h4>Eğitim</h4>
                  <ul>
                    {results.cv_analysis.education?.map((edu, index) => (
                      <li key={index}>{edu}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="analysis-card">
                  <h4>Diller</h4>
                  <div className="languages-list">
                    {results.cv_analysis.languages?.map((lang, index) => (
                      <span key={index} className="language-tag">{lang}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* İş Alanları */}
            <div className="job-areas-section">
              <h3>🎯 Önerilen İş Alanları</h3>
              <div className="job-areas-list">
                {results.job_areas?.map((area, index) => (
                  <div key={index} className="job-area-card">
                    <span className="area-number">{index + 1}</span>
                    <span className="area-name">{area}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* İş İlanları */}
            <div className="job-listings-section">
              <h3>💼 En Uygun İş İlanları</h3>
              <p className="results-summary">
                {results.total_jobs_found} iş ilanı bulundu, en uygun {results.top_matches.length} tanesi listeleniyor.
              </p>
              
              <div className="job-listings">
                {results.top_matches?.map((match, index) => (
                  <div key={index} className="job-card">
                    <div className="job-header">
                      <div className="job-title-section">
                        <h4>{match.job.title}</h4>
                        <p className="company-name">{match.job.company}</p>
                        <p className="job-location">📍 {match.job.location}</p>
                      </div>
                      
                      <div className="match-score">
                        <div 
                          className="score-circle"
                          style={{ backgroundColor: formatMatchScore(match.match_score).color }}
                        >
                          {match.match_score}%
                        </div>
                        <span className="score-text">
                          {formatMatchScore(match.match_score).text}
                        </span>
                      </div>
                    </div>

                    <div className="job-details">
                      <div className="job-description">
                        <h5>İş Açıklaması</h5>
                        <p>{match.job.description}</p>
                      </div>

                      {match.job.requirements && match.job.requirements.length > 0 && (
                        <div className="job-requirements">
                          <h5>Gereksinimler</h5>
                          <ul>
                            {match.job.requirements.map((req, reqIndex) => (
                              <li key={reqIndex}>{req}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div className="match-analysis">
                        <div className="match-reasons">
                          <h5>✅ Uyum Nedenleri</h5>
                          <ul>
                            {match.match_reasons?.map((reason, reasonIndex) => (
                              <li key={reasonIndex}>{reason}</li>
                            ))}
                          </ul>
                        </div>

                        {match.missing_skills && match.missing_skills.length > 0 && (
                          <div className="missing-skills">
                            <h5>⚠️ Eksik Beceriler</h5>
                            <ul>
                              {match.missing_skills.map((skill, skillIndex) => (
                                <li key={skillIndex}>{skill}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {match.recommendations && match.recommendations.length > 0 && (
                          <div className="recommendations">
                            <h5>💡 Öneriler</h5>
                            <ul>
                              {match.recommendations.map((rec, recIndex) => (
                                <li key={recIndex}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {match.job.url && (
                        <div className="job-actions">
                          <a 
                            href={match.job.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="apply-btn"
                          >
                            İlana Git →
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="analysis-info">
              <p>
                <strong>Analiz Tarihi:</strong> {new Date(results.analysis_date).toLocaleString('tr-TR')}
              </p>
              <p>
                <strong>Teknoloji:</strong> CrewAI, LangChain, Gemini AI
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedJobSearch; 