import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { studentVerificationAPI } from '../services/api';

export default function StudentVerification() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState(null);

  // Form fields - both email and document are now required
  const [formData, setFormData] = useState({
    school_email: '',
    document_type: '',
    document_file: null,
    full_name_on_document: '',
    school_name: '',
    enrollment_date: '',
    graduation_date: '',
    date_of_birth: '',
    is_distance_learning: false,
  });

  useEffect(() => {
    loadVerificationStatus();
  }, []);

  const loadVerificationStatus = async () => {
    try {
      const response = await studentVerificationAPI.getStatus();
      setVerificationStatus(response.data);
      
      // If already verified, show success message
      if (response.data.is_verified) {
        setSuccess(true);
      }
    } catch (error) {
      console.error('Failed to load verification status:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    
    if (type === 'file') {
      setFormData(prev => ({
        ...prev,
        [name]: files[0] || null
      }));
    } else if (type === 'checkbox') {
      setFormData(prev => ({
        ...prev,
        [name]: checked
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Method selection removed - both are now required

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      // Validate all required fields (both email and document are required)
      if (!formData.school_email) {
        throw new Error('School email is required');
      }
      
      if (!formData.document_file) {
        throw new Error('Please upload a verification document');
      }
      if (!formData.document_type) {
        throw new Error('Please select a document type');
      }
      if (!formData.full_name_on_document) {
        throw new Error('Please enter your full name as it appears on the document');
      }

      if (!formData.date_of_birth) {
        throw new Error('Date of birth is required');
      }

      // Create FormData for file upload
      const submitData = new FormData();
      submitData.append('date_of_birth', formData.date_of_birth);
      
      // Both email and document are required
      submitData.append('school_email', formData.school_email);
      submitData.append('document_type', formData.document_type);
      submitData.append('document_file', formData.document_file);
      submitData.append('full_name_on_document', formData.full_name_on_document);
      
      if (formData.school_name) {
        submitData.append('school_name', formData.school_name);
      }
      if (formData.enrollment_date) {
        submitData.append('enrollment_date', formData.enrollment_date);
      }
      if (formData.graduation_date) {
        submitData.append('graduation_date', formData.graduation_date);
      }
      submitData.append('is_distance_learning', formData.is_distance_learning);

      const response = await studentVerificationAPI.submit(submitData);
      
      setSuccess(true);
      setVerificationStatus(response.data.verification);
      
      // Redirect to subscriptions after 3 seconds
      setTimeout(() => {
        navigate('/subscriptions');
      }, 3000);
    } catch (error) {
      console.error('Verification submission error:', error);
      
      // Handle detailed error messages from AI verification
      const errorData = error.response?.data;
      let errorMessage = '';
      
      if (errorData?.error_messages && Array.isArray(errorData.error_messages)) {
        // Display multiple error messages as a list
        errorMessage = errorData.error_messages.join('\n');
      } else if (errorData?.error) {
        // Single error message (may contain newlines)
        errorMessage = errorData.error;
      } else {
        errorMessage = errorData?.message || error.message || 'Failed to submit verification. Please try again.';
      }
      
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  // If already verified, show success message
  if (verificationStatus?.is_verified) {
    return (
      <div className="min-h-screen bg-black text-white p-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-green-500/20 border border-green-500 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <svg className="w-8 h-8 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <h2 className="text-2xl font-bold">Student Verification Approved</h2>
            </div>
            <p className="text-gray-300">
              Your student status has been verified. You can now subscribe to the Premium Student plan.
            </p>
            {verificationStatus.verification_date && (
              <p className="text-sm text-gray-400 mt-2">
                Verified on: {new Date(verificationStatus.verification_date).toLocaleDateString()}
              </p>
            )}
            <button
              onClick={() => navigate('/subscriptions')}
              className="mt-4 bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-full font-semibold transition-colors"
            >
              Go to Subscriptions
            </button>
          </div>
        </div>
      </div>
    );
  }

  // If pending, show pending message
  if (verificationStatus?.latest_verification?.status === 'pending') {
    return (
      <div className="min-h-screen bg-black text-white p-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <svg className="w-8 h-8 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <h2 className="text-2xl font-bold">Verification Pending</h2>
            </div>
            <p className="text-gray-300">
              Your student verification request is currently under review. This typically takes a few days.
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Submitted on: {new Date(verificationStatus.latest_verification.created_at).toLocaleDateString()}
            </p>
            <button
              onClick={() => navigate('/subscriptions')}
              className="mt-4 bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-full font-semibold transition-colors"
            >
              Back to Subscriptions
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Student Verification</h1>
          <p className="text-gray-400 text-lg">
            Verify your student status to access Premium Student plan discounts
          </p>
        </div>

        {success && (
          <div className="bg-green-500/20 border border-green-500 rounded-lg p-4 mb-6">
            <p className="text-green-300">
              Verification request submitted successfully! It will be reviewed within a few days.
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2 mb-2">
              <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <h3 className="text-red-400 font-semibold">Verification Failed</h3>
            </div>
            <div className="text-red-300 whitespace-pre-line">
              {error.split('\n').map((line, index) => (
                <p key={index} className={index > 0 ? 'mt-2' : ''}>
                  {line.startsWith('•') ? line : `• ${line}`}
                </p>
              ))}
            </div>
          </div>
        )}

        <div className="bg-[#1a1a1a] rounded-lg p-8">
          <form onSubmit={handleSubmit}>
            {/* Information Banner */}
            <div className="mb-8 bg-purple-500/20 border border-purple-500 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <h3 className="text-purple-300 font-semibold mb-1">Both Email and Document Required</h3>
                  <p className="text-purple-200 text-sm">
                    To complete verification, you must provide both your school email address and a verification document.
                  </p>
                </div>
              </div>
            </div>

            {/* Date of Birth (Required) */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                Date of Birth <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="date_of_birth"
                value={formData.date_of_birth}
                onChange={handleInputChange}
                required
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                You must be at least 13 years old to verify student status
              </p>
            </div>

            {/* Email Verification Fields (REQUIRED) */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                School Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="school_email"
                value={formData.school_email}
                onChange={handleInputChange}
                placeholder="student@university.edu"
                required
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Use your school-issued email. Emails with "+" signs are not accepted.
              </p>
            </div>

            {/* Document Verification Fields (REQUIRED) */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                Document Type <span className="text-red-500">*</span>
              </label>
              <select
                name="document_type"
                value={formData.document_type}
                onChange={handleInputChange}
                required
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
              >
                <option value="">Select document type</option>
                <option value="school_id">School ID Card</option>
                <option value="class_schedule">Class Schedule</option>
                <option value="transcript">Transcript</option>
                <option value="enrollment_letter">Enrollment Verification Letter</option>
              </select>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                Upload Document <span className="text-red-500">*</span>
              </label>
              <input
                type="file"
                name="document_file"
                onChange={handleInputChange}
                accept="image/*,.pdf"
                required
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-500 file:text-white hover:file:bg-purple-600"
              />
              <p className="text-xs text-gray-500 mt-1">
                Upload a clear image or PDF of your verification document
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                Full Name on Document <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="full_name_on_document"
                value={formData.full_name_on_document}
                onChange={handleInputChange}
                placeholder="Enter your full name as it appears on the document"
                required
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Must match the name on your submitted document
              </p>
            </div>

            {/* Optional Fields */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">School Name</label>
              <input
                type="text"
                name="school_name"
                value={formData.school_name}
                onChange={handleInputChange}
                placeholder="Name of your educational institution"
                className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-semibold mb-2">Enrollment Date</label>
                <input
                  type="date"
                  name="enrollment_date"
                  value={formData.enrollment_date}
                  onChange={handleInputChange}
                  className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2">Expected Graduation Date</label>
                <input
                  type="date"
                  name="graduation_date"
                  value={formData.graduation_date}
                  onChange={handleInputChange}
                  className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="is_distance_learning"
                  checked={formData.is_distance_learning}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-purple-500 bg-[#0a0a0a] border-gray-700 rounded focus:ring-purple-500"
                />
                <span className="text-sm">I am enrolled in a distance learning program</span>
              </label>
            </div>

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 rounded-full font-semibold hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Submitting...' : 'Submit Verification'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/subscriptions')}
                className="px-6 border-2 border-gray-700 text-white py-3 rounded-full font-semibold hover:border-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* Information Box */}
        <div className="mt-8 bg-[#1a1a1a] rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Verification Requirements</h3>
          <ul className="space-y-2 text-sm text-gray-400">
            <li className="flex items-start gap-2">
              <span className="text-purple-500 mt-1">•</span>
              <span>You must be at least 13 years old</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500 mt-1">•</span>
              <span>Currently enrolled in a degree- or diploma-granting course</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500 mt-1">•</span>
              <span>Verification typically takes a few days to review</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500 mt-1">•</span>
              <span>Student status must be re-verified every 2 years</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
