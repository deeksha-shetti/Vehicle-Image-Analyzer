import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, RefreshCw, Hash, FileText, Maximize2, Sun, Eye, ShieldCheck, Monitor, AlertOctagon, ChevronDown, ChevronUp } from 'lucide-react';

export default function ResultsView({ resultData, onReset }) {
  const [showFullOcr, setShowFullOcr] = useState(false);

  if (!resultData || !resultData.analysis) {
    return null;
  }

  const { storageUrl, analysis } = resultData;
  const {
    recommendation = 'review',
    dimensions = {},
    blur = {},
    brightness = {},
    duplicate = {},
    screenshotDetection = {},
    tampering = {},
    ocr = {},
    numberPlate = {},
    qualityScore = 0,
    issues = []
  } = analysis;

  const plateText = numberPlate.text || numberPlate.detectedPlate;
  const plateConfidence = numberPlate.confidence ?? 0;

  // Recommendation Badge helper
  const getRecommendationBadge = (rec) => {
    const r = (rec || 'review').toLowerCase();
    if (r === 'accept') {
      return <span className="badge badge-success" style={{ fontSize: '1.1rem', padding: '0.4rem 1.2rem' }}>ACCEPT</span>;
    }
    if (r === 'reject') {
      return <span className="badge badge-danger" style={{ fontSize: '1.1rem', padding: '0.4rem 1.2rem' }}>REJECT</span>;
    }
    return <span className="badge badge-warning" style={{ fontSize: '1.1rem', padding: '0.4rem 1.2rem' }}>REVIEW</span>;
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-green';
    if (score >= 50) return 'score-yellow';
    return 'score-red';
  };

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return <span className="badge badge-danger">High</span>;
      case 'medium':
        return <span className="badge badge-warning">Medium</span>;
      case 'low':
      default:
        return <span className="badge badge-info">Low</span>;
    }
  };

  const formattedHash = duplicate.pHash
    ? `${duplicate.pHash.slice(0, 4)}...${duplicate.pHash.slice(-4)}`
    : 'N/A';

  const generalOcrText = ocr.text || 'No background text detected';
  const isOcrLong = generalOcrText.length > 80;
  const displayedOcrText = isOcrLong && !showFullOcr
    ? `${generalOcrText.slice(0, 80)}...`
    : generalOcrText;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Overall Assessment Card */}
      <div className="card score-card">
        <div style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', fontWeight: 700 }}>
          Overall Assessment
        </div>

        <div style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>
          {getRecommendationBadge(recommendation)}
        </div>

        <div className={`score-badge ${getScoreColorClass(qualityScore)}`}>
          {qualityScore} <span style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>/ 100</span>
        </div>

        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '580px', margin: '0 auto' }}>
          Evaluates image usability, blur severity, lighting quality, duplicate pHash, screenshot/tampering risk, and number plate format.
        </div>

        {/* 3-Category Assessment Summary Checklist */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', width: '100%', marginTop: '2rem', textAlign: 'left' }}>
          {/* Image Quality Category */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--card-border)' }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              Image Quality
            </div>
            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <div>{blur.isBlurred ? '⚠️ Blurry' : '✓ Sharp sharpness'}</div>
              <div>{brightness.isDark ? '⚠️ Dark lighting' : '✓ Good lighting'}</div>
              <div>{dimensions.width < 600 || dimensions.height < 400 ? '⚠️ Low resolution' : '✓ Adequate resolution'}</div>
            </div>
          </div>

          {/* Image Integrity Category */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--card-border)' }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              Image Integrity
            </div>
            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <div>{duplicate.isDuplicate ? '⚠️ Duplicate detected' : '✓ No duplicate'}</div>
              <div>{screenshotDetection.isLikelyScreenshot ? '⚠️ Possible screenshot' : '✓ No screenshot artifacts'}</div>
              <div>{tampering.isSuspicious ? '⚠️ Possible tampering' : '✓ No suspicious manipulation'}</div>
            </div>
          </div>

          {/* Vehicle Identification Category */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--card-border)' }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              Vehicle Identification
            </div>
            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <div>{numberPlate.hasValidIndianNumberPlate && plateText ? `✓ Plate detected` : '⚠️ Plate not confident'}</div>
              <div>{numberPlate.hasValidIndianNumberPlate ? '✓ Valid Indian plate format' : '⚠️ Format uncertain'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="results-grid">
        {/* Dimensions */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Dimensions</div>
            <Maximize2 size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {dimensions.width || 0} × {dimensions.height || 0} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>px</span>
          </div>
          <div className="metric-sub">
            Status: {dimensions.width < 600 || dimensions.height < 400 ? (
              <span className="badge badge-warning">Low Res</span>
            ) : (
              <span className="badge badge-success">Normal</span>
            )}
          </div>
        </div>

        {/* Blur */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Blur Detection</div>
            <Eye size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {blur.severity === 'high' ? (
              <span className="badge badge-danger">Severe Blur</span>
            ) : blur.severity === 'medium' ? (
              <span className="badge badge-warning">Moderate Blur</span>
            ) : (
              <span className="badge badge-success">Sharp</span>
            )}
          </div>
          <div className="metric-sub">
            Blur Score (Variance): {blur.blurScore ?? 'N/A'}
          </div>
        </div>

        {/* Brightness */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Brightness</div>
            <Sun size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {brightness.isDark ? (
              <span className="badge badge-warning">Dark</span>
            ) : (
              <span className="badge badge-success">Good</span>
            )}
          </div>
          <div className="metric-sub">
            Intensity Score: {brightness.brightnessScore ?? 'N/A'}
          </div>
        </div>

        {/* Screenshot / Photo-of-Photo */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Screenshot Check</div>
            <Monitor size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {screenshotDetection.isLikelyScreenshot ? (
              <span className="badge badge-warning">Possible Screenshot</span>
            ) : (
              <span className="badge badge-success">Camera Original</span>
            )}
          </div>
          <div className="metric-sub">
            Confidence: {(screenshotDetection.confidence * 100).toFixed(0)}%
          </div>
        </div>

        {/* Tampering Detection */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Tampering Check</div>
            <AlertOctagon size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {tampering.isSuspicious ? (
              <span className="badge badge-warning">Possible Tampering</span>
            ) : (
              <span className="badge badge-success">No Manipulation</span>
            )}
          </div>
          <div className="metric-sub">
            Confidence: {(tampering.confidence * 100).toFixed(0)}%
          </div>
        </div>

        {/* Duplicate */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Duplicate Check</div>
            <Hash size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value">
            {duplicate.isDuplicate ? (
              <span className="badge badge-warning">Duplicate</span>
            ) : (
              <span className="badge badge-success">No Duplicate</span>
            )}
          </div>
          <div className="metric-sub">
            pHash: <code style={{ color: 'var(--accent-blue)' }}>{formattedHash}</code>
          </div>
        </div>

        {/* Detected Number Plate */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">Number Plate</div>
            <ShieldCheck size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value" style={{ wordBreak: 'break-word', fontSize: '1.2rem', fontWeight: 700 }}>
            {numberPlate.hasValidIndianNumberPlate && plateText ? (
              <div>
                <div style={{ color: 'var(--success)', letterSpacing: '0.05em' }}>
                  {plateText}
                </div>
                <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                  <span className="badge badge-success">VALID INDIAN PLATE</span>
                </div>
              </div>
            ) : (
              <div>
                <div style={{ color: 'var(--warning)', fontSize: '0.95rem' }}>
                  NO CONFIDENT PLATE DETECTED
                </div>
                <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                  <span className="badge badge-warning">Format Uncertain</span>
                </div>
              </div>
            )}
          </div>
          <div className="metric-sub">
            Confidence: {plateConfidence}%
          </div>
        </div>

        {/* General Background OCR Text */}
        <div className="card metric-card">
          <div className="metric-header">
            <div className="metric-title">General OCR</div>
            <FileText size={18} color="var(--accent-blue)" />
          </div>
          <div className="metric-value" style={{ wordBreak: 'break-word', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
            {displayedOcrText}
            {isOcrLong && (
              <button
                onClick={() => setShowFullOcr(!showFullOcr)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  cursor: 'pointer',
                  padding: '0.2rem 0',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.2rem',
                  marginTop: '0.3rem'
                }}
              >
                {showFullOcr ? <>Show less <ChevronUp size={14} /></> : <>Show more <ChevronDown size={14} /></>}
              </button>
            )}
          </div>
          <div className="metric-sub">
            Other background text extracted from image
          </div>
        </div>
      </div>

      {/* Issues & Severity Summary */}
      <div className="card issues-card">
        <div className="issues-title">
          <AlertTriangle size={20} color="var(--warning)" />
          Detected Issues & Severity Summary
        </div>
        {issues.length > 0 ? (
          <div className="issues-list">
            {issues.map((item, idx) => (
              <div key={idx} className="issue-item">
                <span style={{ fontWeight: 500 }}>{item.issue}</span>
                {getSeverityBadge(item.severity)}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--success)', background: 'var(--success-bg)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <CheckCircle size={20} />
            <span style={{ fontWeight: 600 }}>No issues detected. Image passes all usability & integrity checks!</span>
          </div>
        )}
      </div>

      {/* Cloudinary Storage Preview */}
      {storageUrl && (
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="metric-title" style={{ marginBottom: '1rem' }}>Uploaded Image</div>
          <div className="preview-img-wrapper" style={{ margin: '0 auto' }}>
            <img src={storageUrl} alt="Processed Vehicle Image" />
          </div>
        </div>
      )}

      {/* FINAL NUMBER PLATE SHOWCASE AT THE END */}
      <div className="card final-plate-card">
        <div className="plate-title-bar">
          <ShieldCheck size={24} color="var(--accent-blue)" />
          Extracted Number Plate Output
        </div>

        {numberPlate.hasValidIndianNumberPlate && plateText ? (
          <div>
            <div className="hsrp-plate-wrapper">
              <div className="hsrp-plate-box">
                <div className="hsrp-blue-strip">
                  <div className="hsrp-hologram"></div>
                  <div className="hsrp-chakra">⚙</div>
                  <div className="hsrp-ind-text">IND</div>
                </div>
                <div className="hsrp-number-text">
                  {plateText.replace(/^([A-Z]{2})([0-9]{1,2})([A-Z]{1,3})([0-9]{4})$/, '$1 $2 $3 $4')}
                </div>
              </div>
            </div>
            <div className="plate-meta-details">
              <div className="plate-meta-item">
                <span style={{ color: 'var(--text-muted)' }}>Status:</span>
                <span className="badge badge-success">VALID INDIAN HSRP FORMAT</span>
              </div>
              <div className="plate-meta-item">
                <span style={{ color: 'var(--text-muted)' }}>Confidence:</span>
                <strong style={{ color: 'var(--success)' }}>{plateConfidence}%</strong>
              </div>
              <div className="plate-meta-item">
                <span style={{ color: 'var(--text-muted)' }}>Registration:</span>
                <code style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{plateText}</code>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="hsrp-plate-wrapper">
              <div className="hsrp-plate-box unreadable">
                <div className="hsrp-blue-strip">
                  <div className="hsrp-ind-text">IND</div>
                </div>
                <div className="hsrp-unreadable-text">
                  NO CONFIDENT PLATE DETECTED
                </div>
              </div>
            </div>
            <div className="plate-meta-details">
              <div className="plate-meta-item">
                <span style={{ color: 'var(--text-muted)' }}>Status:</span>
                <span className="badge badge-warning">Uncertain / Low Confidence</span>
              </div>
              <div className="plate-meta-item">
                <span style={{ color: 'var(--text-muted)' }}>Tip:</span>
                <span>Ensure license plate is clear, well-lit, and un-obscured</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Another Image */}
      <div style={{ textAlign: 'center', marginTop: '1rem' }}>
        <button className="btn btn-secondary" onClick={onReset}>
          <RefreshCw size={18} />
          Upload Another Image
        </button>
      </div>
    </div>
  );
}

