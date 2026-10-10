import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Upload,
  Camera,
  Trash2,
  Plus,
  Search,
  Check,
  FileText,
  ShieldAlert,
  Info,
  Clock,
  ChevronRight,
  HelpCircle,
  Eye,
  RefreshCw,
} from 'lucide-react';
import { petApi } from '../api/petApi';
import { symptomApi } from '../api/symptomApi';
import { assessmentApi } from '../api/assessmentApi';
import { questionApi } from '../api/questionApi';
import { imageApi } from '../api/imageApi';
import { riskApi } from '../api/riskApi';
import { reportApi } from '../api/reportApi';
import TriageBadge from '../components/common/TriageBadge';
import EmergencyBanner from '../components/common/EmergencyBanner';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

const STEPS = [
  { id: 1, title: 'Select Pet', icon: '🐾' },
  { id: 2, title: 'Symptom Intake', icon: '🩺' },
  { id: 3, title: 'Adaptive Questions', icon: '❓' },
  { id: 4, title: 'Observations', icon: '📋' },
  { id: 5, title: 'Image & CV Analysis', icon: '📷' },
  { id: 6, title: 'Review & Verify', icon: '🔍' },
  { id: 7, title: 'AI Risk Result', icon: '⚡' },
];

export default function AssessmentWizardPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const preselectedPetId = searchParams.get('petId');
  const resumeId = searchParams.get('resumeId');

  // Flow State
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Step 1: Pet
  const [pets, setPets] = useState([]);
  const [selectedPet, setSelectedPet] = useState(null);
  const [assessmentId, setAssessmentId] = useState(resumeId || null);

  // Step 2: Symptoms
  const [symptomCatalog, setSymptomCatalog] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [symptomSearch, setSymptomSearch] = useState('');
  const [assessmentSymptoms, setAssessmentSymptoms] = useState([]);
  const [activeSymptomModal, setActiveSymptomModal] = useState(null);
  const [symptomForm, setSymptomForm] = useState({
    severity: 'moderate',
    duration_value: 1,
    duration_unit: 'days',
    notes: '',
  });

  // Step 3: Dynamic Questions
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [answeredQuestions, setAnsweredQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);

  // Step 4: Observations
  const [observations, setObservations] = useState({
    appetite: 'normal',
    water_intake: 'normal',
    activity_level: 'normal',
    breathing_change: 'normal',
    pain_observed: false,
    general_notes: '',
  });

  // Step 5: Images & CV Quality Gate
  const [uploadedImages, setUploadedImages] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageMeta, setImageMeta] = useState({
    imageType: 'symptom_area',
    bodyPart: '',
    caption: '',
  });
  const [analyzingImageId, setAnalyzingImageId] = useState(null);

  // Step 7: Risk Analysis Results
  const [riskResult, setRiskResult] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  // Initial Load: Fetch Pets & Catalog
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [petsRes, symptomsRes] = await Promise.all([
        petApi.getPets(),
        symptomApi.getSymptoms(),
      ]);

      const petList = petsRes.data || petsRes || [];
      setPets(petList);

      const symList = symptomsRes.data || symptomsRes || [];
      setSymptomCatalog(symList);

      if (resumeId) {
        // Resume existing assessment
        await resumeExistingAssessment(resumeId, petList);
      } else if (preselectedPetId) {
        const found = petList.find((p) => p.id === preselectedPetId);
        if (found) {
          setSelectedPet(found);
        }
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to initialize intake wizard.');
    } finally {
      setLoading(false);
    }
  };

  const resumeExistingAssessment = async (assId, petList) => {
    try {
      const assRes = await assessmentApi.getAssessment(assId);
      const assData = assRes.data || assRes;
      setAssessmentId(assId);

      const foundPet = petList.find((p) => p.id === assData.pet_id);
      if (foundPet) setSelectedPet(foundPet);

      if (assData.symptoms) {
        setAssessmentSymptoms(assData.symptoms);
      }
      if (assData.observations) {
        setObservations({
          appetite: assData.observations.appetite || 'normal',
          water_intake: assData.observations.water_intake || 'normal',
          activity_level: assData.observations.activity_level || 'normal',
          breathing_change: assData.observations.breathing_change || 'normal',
          pain_observed: Boolean(assData.observations.pain_observed),
          general_notes: assData.observations.general_notes || '',
        });
      }

      // Load images if any
      const imgRes = await imageApi.listImages(assId).catch(() => ({ data: [] }));
      setUploadedImages(imgRes.data || imgRes || []);

      setCurrentStep(2);
    } catch (err) {
      console.error('Error resuming assessment:', err);
    }
  };

  // Step 1: Confirm Pet & Create Assessment
  const handleSelectPet = async (pet) => {
    try {
      setSelectedPet(pet);
      setSubmitting(true);
      setError(null);

      if (!assessmentId) {
        const res = await assessmentApi.startAssessment(pet.id);
        const newAss = res.data || res;
        setAssessmentId(newAss.id);
      }
      setCurrentStep(2);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to initialize assessment for this pet.');
    } finally {
      setSubmitting(false);
    }
  };

  // Step 2: Add Symptom
  const handleAddSymptom = async () => {
    if (!activeSymptomModal || !assessmentId) return;
    try {
      setSubmitting(true);
      const payload = {
        symptom_id: activeSymptomModal.id,
        severity: symptomForm.severity,
        duration_value: parseInt(symptomForm.duration_value, 10) || 1,
        duration_unit: symptomForm.duration_unit,
        notes: symptomForm.notes,
      };

      const res = await assessmentApi.addSymptom(assessmentId, payload);
      const added = res.data || res;

      setAssessmentSymptoms((prev) => [
        ...prev,
        {
          ...added,
          symptom: activeSymptomModal,
        },
      ]);

      setActiveSymptomModal(null);
      setSymptomForm({ severity: 'moderate', duration_value: 1, duration_unit: 'days', notes: '' });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to add symptom.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveSymptom = async (symptomAssId) => {
    try {
      await assessmentApi.removeSymptom(assessmentId, symptomAssId);
      setAssessmentSymptoms((prev) => prev.filter((s) => s.id !== symptomAssId));
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to remove symptom.');
    }
  };

  // Step 3: Fetch Questions
  const fetchDynamicQuestions = async () => {
    if (!assessmentId) return;
    try {
      setQuestionsLoading(true);
      const res = await questionApi.getNextQuestions(assessmentId, 6);
      const qList = res.data || res || [];
      setQuestions(qList);

      // Also get answered questions
      const ansRes = await questionApi.getAnswers(assessmentId).catch(() => ({ data: [] }));
      setAnsweredQuestions(ansRes.data || ansRes || []);
    } catch (err) {
      console.error('Failed to load questions:', err);
    } finally {
      setQuestionsLoading(false);
    }
  };

  const handleAnswerSubmit = async (questionId, optionId, answerValue = null) => {
    try {
      const payload = {
        question_id: questionId,
        option_id: optionId || null,
        answer_value: answerValue || null,
      };
      await questionApi.submitAnswer(assessmentId, payload);
      setAnswers((prev) => ({ ...prev, [questionId]: { optionId, answerValue } }));
      // Refresh questions list for adaptive changes
      await fetchDynamicQuestions();
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to record answer.');
    }
  };

  // Step 4: Save Observations
  const handleSaveObservations = async () => {
    try {
      setSubmitting(true);
      setError(null);
      await assessmentApi.upsertObservations(assessmentId, observations);
      setCurrentStep(5);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save clinical observations.');
    } finally {
      setSubmitting(false);
    }
  };

  // Step 5: Images & CV
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadImage = async () => {
    if (!selectedFile || !assessmentId) return;
    try {
      setSubmitting(true);
      setError(null);
      const res = await imageApi.uploadImage(
        assessmentId,
        selectedFile,
        imageMeta.imageType,
        imageMeta.bodyPart,
        imageMeta.caption
      );
      const uploaded = res.data || res;
      setUploadedImages((prev) => [...prev, uploaded]);
      setSelectedFile(null);
      setPreviewUrl(null);
      setImageMeta({ imageType: 'symptom_area', bodyPart: '', caption: '' });

      // Automatically trigger CV analysis
      await handleAnalyzeImage(uploaded.id);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to upload pet image.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAnalyzeImage = async (imageId) => {
    try {
      setAnalyzingImageId(imageId);
      const res = await imageApi.analyzeImage(imageId);
      const analysisData = res.data || res;

      // Update local state with analysis
      setUploadedImages((prev) =>
        prev.map((img) => (img.id === imageId ? { ...img, analysis: analysisData } : img))
      );
    } catch (err) {
      console.error('Image analysis failed:', err);
    } finally {
      setAnalyzingImageId(null);
    }
  };

  const handleDeleteImage = async (imageId) => {
    try {
      await imageApi.deleteImage(imageId);
      setUploadedImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err) {
      alert('Failed to delete image.');
    }
  };

  // Step 6 -> Step 7: Run Risk Analysis
  const handleRunRiskAnalysis = async () => {
    try {
      setSubmitting(true);
      setError(null);
      const res = await riskApi.runRiskAnalysis(assessmentId);
      const result = res.data || res;
      setRiskResult(result);
      setCurrentStep(7);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to complete risk analysis.');
    } finally {
      setSubmitting(false);
    }
  };

  // Step 7: Generate Report
  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      const res = await reportApi.generateReport(assessmentId);
      const report = res.data || res;
      navigate(`/reports/${report.id}`);
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to generate report.');
      setGeneratingReport(false);
    }
  };

  // Filter symptoms
  const filteredSymptoms = symptomCatalog.filter((sym) => {
    const matchesCat = selectedCategory === 'all' || sym.category === selectedCategory;
    const matchesSearch =
      sym.name.toLowerCase().includes(symptomSearch.toLowerCase()) ||
      (sym.description && sym.description.toLowerCase().includes(symptomSearch.toLowerCase()));
    return matchesCat && matchesSearch;
  });

  const categories = ['all', 'digestive', 'respiratory', 'skin_coat', 'musculoskeletal', 'general', 'neurological', 'urinary', 'eyes_ears'];

  if (loading) {
    return (
      <div className="container" style={{ padding: '4rem 1rem' }}>
        <LoadingSpinner message="Loading assessment wizard..." />
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: 'var(--color-bg)', minHeight: 'calc(100vh - 140px)', padding: '2rem 0 4rem' }}>
      <div className="container">
        {/* Wizard Header & Stepper */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.25rem 0', color: 'var(--color-text-main)' }}>
                Pet Health Intake & Triage Assessment
              </h1>
              <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Multi-factor clinical evaluation combining symptoms, adaptive questions, physical observations, and computer vision.
              </p>
            </div>
            {selectedPet && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  padding: '0.5rem 1rem',
                  backgroundColor: 'white',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--color-border)',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <span style={{ fontSize: '1.2rem' }}>
                  {selectedPet.species === 'cat' ? '🐱' : '🐶'}
                </span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', lineHeight: 1 }}>{selectedPet.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {selectedPet.breed || selectedPet.species}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Stepper Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'white',
              borderRadius: 'var(--radius-lg)',
              padding: '0.75rem 1rem',
              border: '1px solid var(--color-border)',
              overflowX: 'auto',
              gap: '0.5rem',
            }}
          >
            {STEPS.map((step, idx) => {
              const isActive = currentStep === step.id;
              const isPast = currentStep > step.id;

              return (
                <React.Fragment key={step.id}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.4rem 0.75rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isActive ? 'var(--color-primary-light)' : 'transparent',
                      color: isActive
                        ? 'var(--color-primary)'
                        : isPast
                        ? 'var(--color-success)'
                        : 'var(--color-text-muted)',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '0.85rem',
                      whiteSpace: 'nowrap',
                      cursor: isPast ? 'pointer' : 'default',
                    }}
                    onClick={() => {
                      if (isPast) setCurrentStep(step.id);
                    }}
                  >
                    <span>{isPast ? '✓' : step.icon}</span>
                    <span>{step.title}</span>
                  </div>
                  {idx < STEPS.length - 1 && (
                    <div
                      style={{
                        height: '2px',
                        width: '16px',
                        backgroundColor: isPast ? 'var(--color-success)' : 'var(--color-border)',
                        flexShrink: 0,
                      }}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {error && (
          <div style={{ marginBottom: '1.5rem' }}>
            <ErrorMessage message={error} onRetry={() => setError(null)} />
          </div>
        )}

        {/* ================= STEP 1: SELECT PET ================= */}
        {currentStep === 1 && (
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Select a Pet for Health Assessment
            </h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Choose which registered pet you are assessing today.
            </p>

            {pets.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
                  You don&apos;t have any registered pets yet. Please add a pet before starting an intake.
                </p>
                <Link to="/pets" className="btn btn-primary">
                  Register Your First Pet
                </Link>
              </div>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                  gap: '1.25rem',
                }}
              >
                {pets.map((pet) => {
                  const isSelected = selectedPet?.id === pet.id;
                  return (
                    <div
                      key={pet.id}
                      onClick={() => setSelectedPet(pet)}
                      style={{
                        padding: '1.25rem',
                        borderRadius: 'var(--radius-lg)',
                        border: isSelected
                          ? '2px solid var(--color-primary)'
                          : '1px solid var(--color-border)',
                        backgroundColor: isSelected ? 'var(--color-primary-light)' : 'var(--color-surface)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                      }}
                    >
                      <div
                        style={{
                          width: '54px',
                          height: '54px',
                          borderRadius: '14px',
                          backgroundColor: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.75rem',
                          boxShadow: 'var(--shadow-sm)',
                        }}
                      >
                        {pet.species === 'cat' ? '🐱' : '🐶'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-main)' }}>
                          {pet.name}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                          {pet.breed || pet.species} • {pet.age_years != null ? `${pet.age_years} yrs` : 'Age unknown'}
                        </div>
                      </div>
                      {isSelected && <CheckCircle2 color="var(--color-primary)" size={22} />}
                    </div>
                  );
                })}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem' }}>
              <button
                disabled={!selectedPet || submitting}
                onClick={() => handleSelectPet(selectedPet)}
                className="btn btn-primary"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem' }}
              >
                {submitting ? 'Initializing...' : 'Proceed to Symptoms'} <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 2: SYMPTOM INTAKE ================= */}
        {currentStep === 2 && (
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem 0' }}>
                  Reported Symptoms for {selectedPet?.name}
                </h2>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', margin: 0 }}>
                  Select all active symptoms observed in your pet.
                </p>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {assessmentSymptoms.length} symptom(s) added
              </div>
            </div>

            {/* Added Symptoms List */}
            {assessmentSymptoms.length > 0 && (
              <div
                style={{
                  marginBottom: '1.75rem',
                  padding: '1.25rem',
                  backgroundColor: 'var(--color-surface)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                  Active Assessment Symptoms:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                  {assessmentSymptoms.map((as) => (
                    <div
                      key={as.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.6rem',
                        backgroundColor: 'white',
                        padding: '0.5rem 0.75rem',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--color-border)',
                        boxShadow: 'var(--shadow-sm)',
                        fontSize: '0.875rem',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{as.symptom?.name || 'Symptom'}</span>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          textTransform: 'uppercase',
                          fontWeight: 700,
                          padding: '0.15rem 0.4rem',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor:
                            as.severity === 'severe'
                              ? 'rgba(239, 68, 68, 0.15)'
                              : as.severity === 'moderate'
                              ? 'rgba(234, 88, 12, 0.15)'
                              : 'rgba(59, 130, 246, 0.15)',
                          color:
                            as.severity === 'severe'
                              ? 'var(--color-danger)'
                              : as.severity === 'moderate'
                              ? 'var(--color-warning)'
                              : 'var(--color-info)',
                        }}
                      >
                        {as.severity}
                      </span>
                      <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                        ({as.duration_value} {as.duration_unit})
                      </span>
                      <button
                        onClick={() => handleRemoveSymptom(as.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--color-danger)',
                          cursor: 'pointer',
                          padding: '0 0.2rem',
                          display: 'flex',
                        }}
                        title="Remove symptom"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Filter & Search Bar */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
              <div style={{ position: 'relative', flex: '1 1 240px' }}>
                <Search
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--color-text-light)',
                  }}
                />
                <input
                  type="text"
                  placeholder="Search symptoms (e.g., vomiting, cough)..."
                  className="form-input"
                  style={{ paddingLeft: '2.25rem' }}
                  value={symptomSearch}
                  onChange={(e) => setSymptomSearch(e.target.value)}
                />
              </div>

              {/* Category Pills */}
              <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className="btn btn-sm"
                    style={{
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: selectedCategory === cat ? 'var(--color-primary)' : 'var(--color-surface)',
                      color: selectedCategory === cat ? 'white' : 'var(--color-text-muted)',
                      border: '1px solid var(--color-border)',
                      textTransform: 'capitalize',
                      fontSize: '0.8rem',
                    }}
                  >
                    {cat.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* Symptoms Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                gap: '0.75rem',
                maxHeight: '360px',
                overflowY: 'auto',
                padding: '0.25rem',
              }}
            >
              {filteredSymptoms.map((sym) => {
                const isAlreadyAdded = assessmentSymptoms.some((s) => s.symptom_id === sym.id);
                return (
                  <div
                    key={sym.id}
                    onClick={() => {
                      if (!isAlreadyAdded) setActiveSymptomModal(sym);
                    }}
                    style={{
                      padding: '0.85rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      border: isAlreadyAdded
                        ? '1px solid var(--color-success)'
                        : '1px solid var(--color-border)',
                      backgroundColor: isAlreadyAdded
                        ? 'rgba(16, 185, 129, 0.05)'
                        : 'var(--color-surface)',
                      cursor: isAlreadyAdded ? 'default' : 'pointer',
                      transition: 'all 0.15s ease',
                      opacity: isAlreadyAdded ? 0.6 : 1,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-main)' }}>
                        {sym.name}
                      </div>
                      {isAlreadyAdded ? (
                        <Check size={16} color="var(--color-success)" />
                      ) : (
                        <Plus size={16} color="var(--color-primary)" />
                      )}
                    </div>
                    {sym.description && (
                      <div
                        style={{
                          fontSize: '0.75rem',
                          color: 'var(--color-text-muted)',
                          marginTop: '0.25rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {sym.description}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Step Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button onClick={() => setCurrentStep(1)} className="btn btn-outline" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <ArrowLeft size={16} /> Back
              </button>
              <button
                disabled={assessmentSymptoms.length === 0}
                onClick={() => {
                  fetchDynamicQuestions();
                  setCurrentStep(3);
                }}
                className="btn btn-primary"
                style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}
              >
                Proceed to Adaptive Questions <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Add Symptom Details Modal */}
        {activeSymptomModal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '1rem',
            }}
          >
            <div
              className="card"
              style={{
                width: '100%',
                maxWidth: '460px',
                padding: '1.75rem',
                backgroundColor: 'white',
                boxShadow: 'var(--shadow-xl)',
              }}
            >
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                Add Symptom: {activeSymptomModal.name}
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem' }}>
                {activeSymptomModal.description || 'Specify how severe and how long this symptom has been observed.'}
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label className="form-label">Severity Level *</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                    {['mild', 'moderate', 'severe'].map((sev) => (
                      <button
                        key={sev}
                        type="button"
                        onClick={() => setSymptomForm({ ...symptomForm, severity: sev })}
                        className="btn btn-sm"
                        style={{
                          textTransform: 'capitalize',
                          backgroundColor:
                            symptomForm.severity === sev
                              ? sev === 'severe'
                                ? 'var(--color-danger)'
                                : sev === 'moderate'
                                ? 'var(--color-warning)'
                                : 'var(--color-info)'
                              : 'var(--color-surface)',
                          color: symptomForm.severity === sev ? 'white' : 'var(--color-text-main)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        {sev}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Duration Value</label>
                    <input
                      type="number"
                      min="1"
                      className="form-input"
                      value={symptomForm.duration_value}
                      onChange={(e) => setSymptomForm({ ...symptomForm, duration_value: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="form-label">Unit</label>
                    <select
                      className="form-input"
                      value={symptomForm.duration_unit}
                      onChange={(e) => setSymptomForm({ ...symptomForm, duration_unit: e.target.value })}
                    >
                      <option value="hours">Hours</option>
                      <option value="days">Days</option>
                      <option value="weeks">Weeks</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="form-label">Observation Notes (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., worse after eating, noticed this morning"
                    value={symptomForm.notes}
                    onChange={(e) => setSymptomForm({ ...symptomForm, notes: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  onClick={() => setActiveSymptomModal(null)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddSymptom}
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Adding...' : 'Add Symptom'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ================= STEP 3: ADAPTIVE QUESTIONS ================= */}
        {currentStep === 3 && (
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem 0' }}>
                  Smart Follow-Up Clinical Questions
                </h2>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', margin: 0 }}>
                  Tailored questions dynamically selected based on reported symptoms and pet profile.
                </p>
              </div>
              <button
                onClick={fetchDynamicQuestions}
                className="btn btn-outline btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                title="Refresh Questions"
              >
                <RefreshCw size={14} /> Refresh
              </button>
            </div>

            {questionsLoading ? (
              <LoadingSpinner message="Evaluating adaptive clinical decision tree..." />
            ) : questions.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '3rem 1rem',
                  backgroundColor: 'var(--color-surface)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <CheckCircle2 size={36} color="var(--color-success)" style={{ marginBottom: '0.75rem' }} />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  All Key Clinical Questions Completed!
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
                  No additional follow-ups required based on the reported symptoms. Proceed to physical observations.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {questions.map((q, idx) => {
                  const currentAnswer = answers[q.id];
                  const hasAnswered = Boolean(currentAnswer) || answeredQuestions.some((a) => a.question_id === q.id);

                  return (
                    <div
                      key={q.id}
                      style={{
                        padding: '1.25rem',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: hasAnswered ? 'rgba(16, 185, 129, 0.04)' : 'var(--color-surface)',
                        border: hasAnswered
                          ? '1px solid var(--color-success)'
                          : '1px solid var(--color-border)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.75rem' }}>
                        <div>
                          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase' }}>
                            Question {idx + 1}
                          </div>
                          <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--color-text-main)', marginTop: '0.1rem' }}>
                            {q.question_text}
                          </div>
                          {q.explanation && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                              💡 {q.explanation}
                            </div>
                          )}
                        </div>
                        {hasAnswered && (
                          <span
                            style={{
                              fontSize: '0.75rem',
                              color: 'var(--color-success)',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                            }}
                          >
                            <Check size={14} /> Answered
                          </span>
                        )}
                      </div>

                      {/* Options */}
                      {q.options && q.options.length > 0 ? (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem' }}>
                          {q.options.map((opt) => {
                            const isOptSelected = currentAnswer?.optionId === opt.id;
                            return (
                              <button
                                key={opt.id}
                                type="button"
                                onClick={() => handleAnswerSubmit(q.id, opt.id, opt.label)}
                                className="btn btn-sm"
                                style={{
                                  textAlign: 'left',
                                  padding: '0.6rem 0.85rem',
                                  backgroundColor: isOptSelected ? 'var(--color-primary)' : 'white',
                                  color: isOptSelected ? 'white' : 'var(--color-text-main)',
                                  border: isOptSelected
                                    ? '1px solid var(--color-primary)'
                                    : '1px solid var(--color-border)',
                                  borderRadius: 'var(--radius-md)',
                                  fontSize: '0.85rem',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                }}
                              >
                                <span>{opt.label || opt.text}</span>
                                {opt.risk_weight > 2 && (
                                  <span style={{ fontSize: '0.65rem', color: isOptSelected ? '#fecaca' : '#dc2626' }}>
                                    ⚠️ High Risk
                                  </span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        /* Default Yes/No fallback */
                        <div style={{ display: 'flex', gap: '0.75rem' }}>
                          {['Yes', 'No', 'Unsure'].map((val) => (
                            <button
                              key={val}
                              type="button"
                              onClick={() => handleAnswerSubmit(q.id, null, val)}
                              className="btn btn-outline btn-sm"
                            >
                              {val}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button onClick={() => setCurrentStep(2)} className="btn btn-outline" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <ArrowLeft size={16} /> Back to Symptoms
              </button>
              <button
                onClick={() => setCurrentStep(4)}
                className="btn btn-primary"
                style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}
              >
                Proceed to Observations <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 4: CLINICAL OBSERVATIONS ================= */}
        {currentStep === 4 && (
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              General Clinical Observations
            </h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Record vital behavioral, nutritional, and physical indicators for {selectedPet?.name}.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
              {/* Appetite */}
              <div>
                <label className="form-label">Appetite Status</label>
                <select
                  className="form-input"
                  value={observations.appetite}
                  onChange={(e) => setObservations({ ...observations, appetite: e.target.value })}
                >
                  <option value="normal">Normal (Eating regularly)</option>
                  <option value="decreased">Decreased (Eating less than usual)</option>
                  <option value="absent">Absent / Anorexia (Refusing food completely)</option>
                  <option value="increased">Increased (Excessive hunger)</option>
                </select>
              </div>

              {/* Water Intake */}
              <div>
                <label className="form-label">Water Intake</label>
                <select
                  className="form-input"
                  value={observations.water_intake}
                  onChange={(e) => setObservations({ ...observations, water_intake: e.target.value })}
                >
                  <option value="normal">Normal (Typical consumption)</option>
                  <option value="decreased">Decreased (Drinking significantly less)</option>
                  <option value="increased">Increased (Excessive drinking / Polydipsia)</option>
                </select>
              </div>

              {/* Activity Level */}
              <div>
                <label className="form-label">Activity Level</label>
                <select
                  className="form-input"
                  value={observations.activity_level}
                  onChange={(e) => setObservations({ ...observations, activity_level: e.target.value })}
                >
                  <option value="normal">Normal (Alert and playful)</option>
                  <option value="lethargic">Lethargic (Sluggish, slow to respond)</option>
                  <option value="depressed">Depressed (Withdrawn, unengaged)</option>
                  <option value="hyperactive">Hyperactive / Agitated</option>
                </select>
              </div>

              {/* Breathing Change */}
              <div>
                <label className="form-label">Breathing / Respiratory Effort</label>
                <select
                  className="form-input"
                  value={observations.breathing_change}
                  onChange={(e) => setObservations({ ...observations, breathing_change: e.target.value })}
                >
                  <option value="normal">Normal (Smooth, effortless breathing)</option>
                  <option value="rapid">Rapid / Tachypnea (Elevated respiratory rate)</option>
                  <option value="shallow">Shallow breathing</option>
                  <option value="labored">Labored / Dyspnea (Open-mouth or abdominal effort)</option>
                </select>
              </div>
            </div>

            {/* Pain Indicator */}
            <div
              style={{
                marginTop: '1.5rem',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: observations.pain_observed ? 'rgba(239, 68, 68, 0.08)' : 'var(--color-surface)',
                border: observations.pain_observed
                  ? '1px solid rgba(239, 68, 68, 0.3)'
                  : '1px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--color-text-main)' }}>
                  Is {selectedPet?.name} showing visible signs of acute pain?
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  Signs include vocalizing, guarding areas, stiffness, limping, trembling, or aggression when touched.
                </div>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={observations.pain_observed}
                  onChange={(e) => setObservations({ ...observations, pain_observed: e.target.checked })}
                  style={{ width: '18px', height: '18px' }}
                />
                Pain Observed
              </label>
            </div>

            {/* Additional Notes */}
            <div style={{ marginTop: '1.25rem' }}>
              <label className="form-label">Additional Observations / Owner Notes</label>
              <textarea
                className="form-input"
                rows={3}
                placeholder="Describe any other unusual behaviors, posture changes, or contextual details..."
                value={observations.general_notes}
                onChange={(e) => setObservations({ ...observations, general_notes: e.target.value })}
              />
            </div>

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button onClick={() => setCurrentStep(3)} className="btn btn-outline" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <ArrowLeft size={16} /> Back to Questions
              </button>
              <button
                disabled={submitting}
                onClick={handleSaveObservations}
                className="btn btn-primary"
                style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}
              >
                {submitting ? 'Saving...' : 'Proceed to Image Upload'} <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 5: PET IMAGE UPLOAD & CV QUALITY GATE ================= */}
        {currentStep === 5 && (
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.25rem 0' }}>
                  Pet Image Upload & Computer Vision Quality Gate
                </h2>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', margin: 0 }}>
                  Upload clear photos of affected areas (skin, eyes, posture) for automated visual quality assessment and feature inspection.
                </p>
              </div>
              <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem', borderRadius: 'var(--radius-full)', backgroundColor: 'var(--color-surface-hover)' }}>
                Optional Step
              </span>
            </div>

            {/* Upload Box */}
            <div
              style={{
                border: '2px dashed var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: 'var(--color-surface)',
                marginBottom: '1.5rem',
              }}
            >
              {previewUrl ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                  <img
                    src={previewUrl}
                    alt="Upload Preview"
                    style={{
                      maxHeight: '220px',
                      maxWidth: '100%',
                      borderRadius: 'var(--radius-md)',
                      objectFit: 'contain',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  />
                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <select
                      className="form-input"
                      style={{ width: 'auto' }}
                      value={imageMeta.imageType}
                      onChange={(e) => setImageMeta({ ...imageMeta, imageType: e.target.value })}
                    >
                      <option value="symptom_area">Affected Symptom Area</option>
                      <option value="full_body">Full Body / Posture</option>
                      <option value="eyes">Eyes / Facial</option>
                      <option value="skin_coat">Skin & Coat / Lesion</option>
                      <option value="mouth_teeth">Mouth / Gums</option>
                    </select>

                    <input
                      type="text"
                      placeholder="Body part (e.g., right ear, belly)"
                      className="form-input"
                      style={{ width: '220px' }}
                      value={imageMeta.bodyPart}
                      onChange={(e) => setImageMeta({ ...imageMeta, bodyPart: e.target.value })}
                    />

                    <button
                      disabled={submitting}
                      onClick={handleUploadImage}
                      className="btn btn-primary btn-sm"
                      style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                      <Upload size={14} /> {submitting ? 'Analyzing...' : 'Upload & Run CV Analysis'}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        setPreviewUrl(null);
                      }}
                      className="btn btn-outline btn-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <Camera size={42} color="var(--color-text-light)" style={{ marginBottom: '0.75rem' }} />
                  <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.25rem' }}>
                    Choose an image from your device
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    Supports PNG, JPG, or JPEG up to 10MB. Clear lighting and in-focus images provide best quality gate results.
                  </p>
                  <label className="btn btn-primary btn-sm" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Upload size={15} /> Select File
                    <input
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={handleFileChange}
                    />
                  </label>
                </div>
              )}
            </div>

            {/* Uploaded Images & CV Results */}
            {uploadedImages.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                  Analyzed Images ({uploadedImages.length})
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
                  {uploadedImages.map((img) => {
                    const cv = img.analysis || img.analysis_result;
                    const isAnalyzing = analyzingImageId === img.id;

                    return (
                      <div
                        key={img.id}
                        style={{
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-border)',
                          backgroundColor: 'var(--color-surface)',
                          padding: '1rem',
                        }}
                      >
                        <div style={{ display: 'flex', gap: '1rem' }}>
                          <img
                            src={img.file_url || `/api/v1/assessment-images/${img.id}/file`}
                            alt="Uploaded pet inspection"
                            style={{
                              width: '90px',
                              height: '90px',
                              objectFit: 'cover',
                              borderRadius: 'var(--radius-md)',
                              backgroundColor: '#e2e8f0',
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.85rem', textTransform: 'capitalize' }}>
                                {img.image_type?.replace('_', ' ') || 'Symptom Area'}
                              </span>
                              <button
                                onClick={() => handleDeleteImage(img.id)}
                                style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer' }}
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                              Part: {img.body_part || 'General'}
                            </div>

                            {/* CV Quality Gate Badge & Results */}
                            {cv ? (
                              <div style={{ marginTop: '0.5rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.35rem' }}>
                                  <span
                                    style={{
                                      fontSize: '0.7rem',
                                      fontWeight: 700,
                                      padding: '0.15rem 0.45rem',
                                      borderRadius: 'var(--radius-sm)',
                                      backgroundColor:
                                        cv.quality_gate === 'PASSED' || cv.quality_gate_passed === true
                                          ? 'rgba(16, 185, 129, 0.15)'
                                          : 'rgba(239, 68, 68, 0.15)',
                                      color:
                                        cv.quality_gate === 'PASSED' || cv.quality_gate_passed === true
                                          ? 'var(--color-success)'
                                          : 'var(--color-danger)',
                                    }}
                                  >
                                    Quality Gate: {cv.quality_gate === 'PASSED' || cv.quality_gate_passed === true ? 'PASSED' : 'REQUIRES BETTER PHOTO'}
                                  </span>
                                  {cv.quality_score != null && (
                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                      Quality Score: {(cv.quality_score * 100).toFixed(0)}%
                                    </span>
                                  )}
                                </div>

                                {/* Quality Failure Reasons & Actionable Guidance */}
                                {(cv.quality_gate === 'REQUIRES_BETTER_IMAGE' || cv.reasons?.length > 0) && (
                                  <div
                                    style={{
                                      padding: '0.6rem 0.75rem',
                                      borderRadius: 'var(--radius-sm)',
                                      backgroundColor: '#fffbeb',
                                      border: '1px solid #fde68a',
                                      fontSize: '0.75rem',
                                      color: '#92400e',
                                      marginBottom: '0.5rem',
                                    }}
                                  >
                                    {cv.reasons && cv.reasons.length > 0 && (
                                      <div style={{ marginBottom: '0.35rem' }}>
                                        <strong>Quality Issues:</strong> {cv.reasons.join('; ')}
                                      </div>
                                    )}
                                    {cv.actionable_guidance && cv.actionable_guidance.length > 0 && (
                                      <div>
                                        <strong>💡 Actionable Tips:</strong>
                                        <ul style={{ margin: '0.2rem 0 0 1rem', padding: 0 }}>
                                          {cv.actionable_guidance.map((tip, tIdx) => (
                                            <li key={tIdx}>{tip}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Quality Metrics Tags */}
                                {cv.quality_metrics && (
                                  <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.4rem', fontSize: '0.7rem' }}>
                                    <span style={{ padding: '0.1rem 0.35rem', backgroundColor: '#f1f5f9', borderRadius: '3px', color: '#475569' }}>
                                      {cv.quality_metrics.width}x{cv.quality_metrics.height}px
                                    </span>
                                    <span style={{ padding: '0.1rem 0.35rem', backgroundColor: cv.quality_metrics.is_well_lit ? '#ecfdf5' : '#fef2f2', borderRadius: '3px', color: cv.quality_metrics.is_well_lit ? '#065f46' : '#991b1b' }}>
                                      Lighting: {cv.quality_metrics.is_well_lit ? 'Good' : 'Sub-optimal'}
                                    </span>
                                    <span style={{ padding: '0.1rem 0.35rem', backgroundColor: cv.quality_metrics.is_sharp !== false ? '#ecfdf5' : '#fef2f2', borderRadius: '3px', color: cv.quality_metrics.is_sharp !== false ? '#065f46' : '#991b1b' }}>
                                      Focus: {cv.quality_metrics.is_sharp !== false ? 'Sharp' : 'Blurry'}
                                    </span>
                                  </div>
                                )}

                                {/* Observations list */}
                                {cv.observations && cv.observations.length > 0 && (
                                  <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '0.3rem' }}>
                                    {cv.observations.map((obs, oIdx) => (
                                      <div key={oIdx} style={{ color: 'var(--color-text-main)' }}>
                                        <strong>{obs.observation_label?.replace(/_/g, ' ')}:</strong> {obs.description}
                                        {obs.observation_label === 'ELEVATED_ERYTHEMA_DETECTED' && (
                                          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginTop: '0.1rem' }}>
                                            * Measured visual redness; early computational indicator, not a definitive veterinary diagnosis.
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div style={{ marginTop: '0.5rem' }}>
                                <button
                                  disabled={isAnalyzing}
                                  onClick={() => handleAnalyzeImage(img.id)}
                                  className="btn btn-outline btn-sm"
                                  style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                                >
                                  {isAnalyzing ? 'Analyzing...' : 'Run CV Analysis'}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
              <button onClick={() => setCurrentStep(4)} className="btn btn-outline" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <ArrowLeft size={16} /> Back to Observations
              </button>
              <button
                onClick={() => setCurrentStep(6)}
                className="btn btn-primary"
                style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}
              >
                Proceed to Review & Verification <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 6: REVIEW & VERIFY ================= */}
        {currentStep === 6 && (
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Review Health Assessment Summary
            </h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Verify all entered clinical parameters before executing the AI Health Risk Analysis Engine.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
              {/* Pet Info */}
              <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                  🐾 Patient Information
                </div>
                <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div><strong>Name:</strong> {selectedPet?.name}</div>
                  <div><strong>Species/Breed:</strong> {selectedPet?.species} • {selectedPet?.breed || 'Mixed'}</div>
                  <div><strong>Age:</strong> {selectedPet?.age_years != null ? `${selectedPet.age_years} yrs` : 'Unknown'}</div>
                  <div><strong>Weight:</strong> {selectedPet?.weight_kg != null ? `${selectedPet.weight_kg} kg` : 'Unknown'}</div>
                </div>
              </div>

              {/* Symptoms */}
              <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                  🩺 Active Symptoms ({assessmentSymptoms.length})
                </div>
                <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {assessmentSymptoms.map((as) => (
                    <div key={as.id}>
                      • <strong>{as.symptom?.name || 'Symptom'}</strong> ({as.severity}, {as.duration_value} {as.duration_unit})
                    </div>
                  ))}
                </div>
              </div>

              {/* Observations */}
              <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                  📋 Key Observations
                </div>
                <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div><strong>Appetite:</strong> {observations.appetite}</div>
                  <div><strong>Water Intake:</strong> {observations.water_intake}</div>
                  <div><strong>Activity:</strong> {observations.activity_level}</div>
                  <div><strong>Breathing:</strong> {observations.breathing_change}</div>
                  <div><strong>Pain Observed:</strong> {observations.pain_observed ? '⚠️ Yes' : 'No'}</div>
                </div>
              </div>

              {/* Images */}
              <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                  📷 Images Uploaded
                </div>
                <div style={{ fontSize: '0.85rem' }}>
                  {uploadedImages.length > 0 ? (
                    <div>{uploadedImages.length} image(s) processed with CV quality gate evaluation.</div>
                  ) : (
                    <div style={{ color: 'var(--color-text-muted)' }}>No images attached (optional).</div>
                  )}
                </div>
              </div>
            </div>

            {/* Execution CTA Banner */}
            <div
              style={{
                padding: '1.5rem',
                borderRadius: 'var(--radius-lg)',
                background: 'linear-gradient(135deg, var(--color-primary-light), white)',
                border: '1px solid var(--color-primary-subtle, rgba(2, 132, 199, 0.2))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 0.25rem 0', color: 'var(--color-primary)' }}>
                  Ready for AI Health Risk Analysis?
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-main)', margin: 0 }}>
                  The engine will calculate transparent risk scores, verify emergency hard-stops, and explain contributing factors.
                </p>
              </div>

              <button
                disabled={submitting}
                onClick={handleRunRiskAnalysis}
                className="btn btn-primary"
                style={{ padding: '0.85rem 1.75rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                {submitting ? 'Analyzing Risk...' : 'Run AI Risk Analysis'} <ArrowRight size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '1.5rem' }}>
              <button onClick={() => setCurrentStep(5)} className="btn btn-outline" style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <ArrowLeft size={16} /> Back to Images
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 7: AI RISK RESULT & REPORT GENERATION ================= */}
        {currentStep === 7 && riskResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Emergency Hard Stop Banner */}
            {riskResult.is_emergency && (
              <EmergencyBanner
                message={riskResult.emergency_reason || 'Immediate veterinary medical attention recommended.'}
              />
            )}

            {/* Main Risk Summary Card */}
            <div className="card" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0 }}>
                      AI Risk Assessment Result
                    </h2>
                    <TriageBadge level={riskResult.triage_level} />
                  </div>
                  <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', margin: 0 }}>
                    Transparent multi-factor triage score computed for {selectedPet?.name}.
                  </p>
                </div>

                {/* Score Dial / Pill */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '1rem 1.5rem',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor:
                      riskResult.triage_level === 'emergency' || riskResult.triage_level === 'high'
                        ? 'rgba(239, 68, 68, 0.1)'
                        : riskResult.triage_level === 'moderate'
                        ? 'rgba(234, 88, 12, 0.1)'
                        : 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
                    Risk Score
                  </div>
                  <div
                    style={{
                      fontSize: '2.5rem',
                      fontWeight: 900,
                      lineHeight: 1.1,
                      color:
                        riskResult.triage_level === 'emergency' || riskResult.triage_level === 'high'
                          ? 'var(--color-danger)'
                          : riskResult.triage_level === 'moderate'
                          ? 'var(--color-warning)'
                          : 'var(--color-success)',
                    }}
                  >
                    {riskResult.risk_score}
                    <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>/100</span>
                  </div>
                </div>
              </div>

              {/* Clinical Data Quality & Contradiction Notices */}
              {((riskResult.data_quality_warnings && riskResult.data_quality_warnings.length > 0) ||
                (riskResult.factor_breakdown?.data_quality_warnings && riskResult.factor_breakdown.data_quality_warnings.length > 0)) && (
                <div
                  style={{
                    marginBottom: '1.5rem',
                    padding: '1rem 1.25rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: '#fffbeb',
                    border: '1px solid #fde68a',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#92400e', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>⚠️</span> Clinical Evidence Uncertainty & Quality Notices
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {(riskResult.data_quality_warnings || riskResult.factor_breakdown.data_quality_warnings).map((w, wIdx) => (
                      <div key={wIdx} style={{ fontSize: '0.825rem', color: '#78350f', lineHeight: 1.4 }}>
                        <strong>{w.title}:</strong> {w.message}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Contributing Factors & Explainability */}
              <div style={{ marginBottom: '1.75rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                  Explainable Factor Attribution & Evidence Sources
                </h3>

                {(riskResult.structured_factors && riskResult.structured_factors.length > 0) ||
                (riskResult.factor_breakdown?.structured_factors && riskResult.factor_breakdown.structured_factors.length > 0) ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {(riskResult.structured_factors || riskResult.factor_breakdown.structured_factors).map((sf, sIdx) => {
                      const isEmergency = sf.direction === 'emergency_override' || sf.is_emergency_flag;
                      const isReassuring = sf.direction === 'reassuring';
                      const isUnknown = sf.direction === 'unknown' || sf.status === 'UNKNOWN';

                      return (
                        <div
                          key={sIdx}
                          style={{
                            padding: '0.85rem 1.15rem',
                            borderRadius: 'var(--radius-md)',
                            backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.05)' : isReassuring ? 'rgba(16, 185, 129, 0.05)' : 'var(--color-surface)',
                            border: `1px solid ${isEmergency ? 'rgba(239, 68, 68, 0.25)' : isReassuring ? 'rgba(16, 185, 129, 0.25)' : 'var(--color-border)'}`,
                            fontSize: '0.875rem',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.35rem' }}>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 700, color: 'var(--color-text-main)' }}>{sf.factor_name}</span>
                                <span
                                  style={{
                                    fontSize: '0.7rem',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    padding: '0.15rem 0.45rem',
                                    borderRadius: 'var(--radius-sm)',
                                    backgroundColor: 'rgba(2, 132, 199, 0.12)',
                                    color: 'var(--color-primary)',
                                  }}
                                >
                                  {sf.source?.replace('_', ' ') || 'CLINICAL'}
                                </span>
                                <span
                                  style={{
                                    fontSize: '0.7rem',
                                    fontWeight: 700,
                                    padding: '0.15rem 0.45rem',
                                    borderRadius: 'var(--radius-sm)',
                                    backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.15)' : isReassuring ? 'rgba(16, 185, 129, 0.15)' : isUnknown ? 'rgba(148, 163, 184, 0.2)' : 'rgba(234, 88, 12, 0.15)',
                                    color: isEmergency ? 'var(--color-danger)' : isReassuring ? 'var(--color-success)' : isUnknown ? '#64748b' : 'var(--color-warning)',
                                  }}
                                >
                                  {isEmergency ? 'EMERGENCY OVERRIDE' : isReassuring ? 'REASSURING' : isUnknown ? 'UNKNOWN STATUS' : 'RISK INCREASING'}
                                </span>
                              </div>
                              <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                                Finding: <strong>{sf.finding}</strong>
                              </div>
                            </div>

                            {sf.contribution_pts !== null && sf.contribution_pts !== undefined ? (
                              <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--color-primary)', whiteSpace: 'nowrap' }}>
                                +{sf.contribution_pts} pts
                              </span>
                            ) : isEmergency ? (
                              <span style={{ fontWeight: 800, fontSize: '0.75rem', color: 'var(--color-danger)', whiteSpace: 'nowrap' }}>
                                {"FLOOR >= 90"}
                              </span>
                            ) : null}
                          </div>

                          {sf.rationale && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-main)', marginTop: '0.35rem', lineHeight: 1.4 }}>
                              💡 <em>{sf.rationale}</em>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (riskResult.key_factors || riskResult.contributing_factors) && (riskResult.key_factors || riskResult.contributing_factors).length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {(riskResult.key_factors || riskResult.contributing_factors).map((factor, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '0.75rem 1rem',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: 'var(--color-surface)',
                          border: '1px solid var(--color-border)',
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                        }}
                      >
                        <span>•</span>
                        <span>{typeof factor === 'string' ? factor : factor.description || factor.name}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    Risk score calculated based on baseline symptom profile and owner-reported history.
                  </p>
                )}
              </div>

              {/* Recommended Action */}
              {riskResult.recommended_action && (
                <div
                  style={{
                    padding: '1rem 1.25rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(2, 132, 199, 0.08)',
                    border: '1px solid rgba(2, 132, 199, 0.2)',
                    marginBottom: '1.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--color-primary)', marginBottom: '0.25rem' }}>
                    Recommended Clinical Next Steps:
                  </div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-main)' }}>
                    {riskResult.recommended_action}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  paddingTop: '1.5rem',
                  borderTop: '1px solid var(--color-border)',
                }}
              >
                <button
                  onClick={() => navigate('/dashboard')}
                  className="btn btn-outline"
                >
                  Return to Dashboard
                </button>

                <button
                  disabled={generatingReport}
                  onClick={handleGenerateReport}
                  className="btn btn-primary"
                  style={{ padding: '0.85rem 1.75rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <FileText size={18} />
                  {generatingReport ? 'Generating Report...' : 'Generate Official Veterinary Report'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
