import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { subscriptionsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const planColors = {
  individual: 'from-pink-500 to-pink-600',
  student: 'from-purple-500 to-purple-600',
  duo: 'from-orange-500 to-orange-600',
  family: 'from-blue-500 to-blue-600',
};

const planHeaderColors = {
  individual: 'bg-pink-500',
  student: 'bg-purple-500',
  duo: 'bg-orange-500',
  family: 'bg-blue-500',
};

export default function Subscriptions() {
  const navigate = useNavigate();
  const { user, refreshUser, isArtist } = useAuth();
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);
  const [error, setError] = useState(null);

  // Redirect artists away from subscriptions page
  useEffect(() => {
    if (isArtist || user?.role === 2 || user?.user?.role === 2 || user?.profile_type === 2) {
      navigate('/');
      return;
    }
  }, [isArtist, user, navigate]);

  useEffect(() => {
    loadPlans();
  }, []);

  // Load current subscription after plans are loaded
  useEffect(() => {
    if (plans.length > 0) {
      loadCurrentSubscription();
    }
  }, [plans, user]);

  const loadPlans = async () => {
    try {
      const response = await subscriptionsAPI.getAll();
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to load plans:', error);
      setError('Failed to load subscription plans');
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentSubscription = async () => {
    try {
      const response = await subscriptionsAPI.getCurrent();
      if (response.data.subscription) {
        setCurrentSubscription(response.data.subscription);
        return;
      }
    } catch (error) {
      console.error('Failed to load current subscription from API:', error);
    }
    
    // Fallback: check user profile for subscription info
    const subscriptionPlanName = user?.subscription_plan_name || user?.subscription_plan?.name;
    const subscriptionStatus = user?.subscription_status;
    
    if (subscriptionPlanName && (subscriptionStatus === 'active' || subscriptionStatus === 'trialing')) {
      // Find the plan in the plans list by name
      const plan = plans.find(p => p.name === subscriptionPlanName);
      if (plan) {
        setCurrentSubscription(plan);
        return;
      }
    }
    
    setCurrentSubscription(null);
  };

  const handleSubscribe = async (planId) => {
    setSubscribing(true);
    setError(null);
    try {
      const frontendUrl = window.location.origin;
      const response = await subscriptionsAPI.subscribe(planId, frontendUrl);
      
      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        // Fallback if no checkout URL (shouldn't happen)
        alert('Subscription activated successfully!');
        await loadCurrentSubscription();
        await refreshUser();
      }
    } catch (error) {
      console.error('Failed to subscribe:', error);
      const errorData = error.response?.data;
      
      // Check if student verification is required
      if (errorData?.requires_verification) {
        if (errorData.verification_status === 'not_submitted') {
          // Redirect to verification page
          navigate('/student-verification');
          return;
        } else if (errorData.verification_status === 'pending') {
          setError(errorData.error || 'Your student verification is pending review. Please wait for approval.');
        }
      } else {
        setError(errorData?.error || 'Failed to subscribe. Please try again.');
      }
      setSubscribing(false);
    }
  };

  const formatPrice = (price, currency = 'USD') => {
    // Convert to PKR (Rs) for display
    const priceInPKR = parseFloat(price) * 280; // Approximate conversion
    return `Rs ${Math.round(priceInPKR)}`;
  };

  const getPlanType = (planType) => {
    return planType.toLowerCase();
  };

  const hasTrial = (planType) => {
    return planType.toLowerCase() === 'individual' || planType.toLowerCase() === 'student';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Loading subscription plans...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4">Choose your Premium</h1>
          <p className="text-gray-400 text-lg">Listen without limits on your phone, speaker, and other devices.</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded flex items-center justify-between">
            <span>{error}</span>
            {error.includes('verification') && !error.includes('pending') && (
              <button
                onClick={() => navigate('/student-verification')}
                className="ml-4 bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-full font-semibold transition-colors whitespace-nowrap"
              >
                Verify Now
              </button>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const planType = getPlanType(plan.plan_type);
            // Check if this is the current plan by comparing IDs or names
            // Also check user profile directly as fallback
            const userPlanName = user?.subscription_plan_name || user?.subscription_plan?.name;
            const userSubscriptionStatus = user?.subscription_status;
            const isCurrentPlan = currentSubscription && (
              currentSubscription.id === plan.id || 
              currentSubscription.name === plan.name
            ) || (
              userPlanName === plan.name && 
              (userSubscriptionStatus === 'active' || userSubscriptionStatus === 'trialing')
            );
            const showTrial = hasTrial(plan.plan_type);

            return (
              <div
                key={plan.id}
                className={`bg-[#1a1a1a] rounded-lg overflow-hidden border-2 ${
                  isCurrentPlan ? 'border-green-500' : 'border-gray-800'
                } hover:border-gray-700 transition-all`}
              >
                {/* Header Banner */}
                {showTrial && (
                  <div className={`${planHeaderColors[planType] || 'bg-gray-600'} text-white text-center py-2 text-sm font-semibold`}>
                    Rs 0 for 1 month
                  </div>
                )}

                <div className="p-6">
                  {/* Plan Title */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                        <svg className="w-5 h-5 text-black" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </div>
                      <span className="text-xs text-gray-400 uppercase tracking-wider">Premium</span>
                    </div>
                    <h3 className="text-2xl font-bold">{plan.name}</h3>
                  </div>

                  {/* Pricing */}
                  <div className="mb-6">
                    {showTrial ? (
                      <>
                        <div className="text-3xl font-bold mb-1">Rs 0 for 1 month</div>
                        <div className="text-gray-400">
                          {formatPrice(plan.price)}/month after
                        </div>
                      </>
                    ) : (
                      <div className="text-3xl font-bold">{formatPrice(plan.price)}/month</div>
                    )}
                  </div>

                  {/* Features */}
                  <ul className="space-y-3 mb-6">
                    {plan.plan_type.toLowerCase() === 'individual' && (
                      <>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>1 Premium account</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Cancel anytime</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Subscribe or one-time payment</span>
                        </li>
                      </>
                    )}
                    {plan.plan_type.toLowerCase() === 'student' && (
                      <>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>1 verified Premium account</span>
                        </li>
                        {!user?.is_student && (
                          <li className="flex items-start gap-2 text-yellow-400">
                            <svg className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            <span>Student verification required</span>
                          </li>
                        )}
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Discount for eligible students</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Cancel anytime</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Subscribe or one-time payment</span>
                        </li>
                      </>
                    )}
                    {plan.plan_type.toLowerCase() === 'duo' && (
                      <>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>2 Premium accounts</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Cancel anytime</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Subscribe or one-time payment</span>
                        </li>
                      </>
                    )}
                    {plan.plan_type.toLowerCase() === 'family' && (
                      <>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Up to 6 Premium accounts</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Parental controls for the plan manager</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Cancel anytime</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Subscribe or one-time payment</span>
                        </li>
                      </>
                    )}
                  </ul>

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    {isCurrentPlan ? (
                      <button
                        disabled
                        className="w-full bg-gray-700 text-gray-400 py-3 rounded-full font-semibold cursor-not-allowed"
                      >
                        Current Plan
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSubscribe(plan.id)}
                        disabled={subscribing}
                        className={`w-full bg-gradient-to-r ${planColors[planType] || 'from-green-500 to-green-600'} text-white py-3 rounded-full font-semibold hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {subscribing ? 'Processing...' : showTrial ? `Try 1 month for Rs 0` : `Get ${plan.name}`}
                      </button>
                    )}
                    <button className="w-full border-2 border-gray-600 text-white py-3 rounded-full font-semibold hover:border-gray-500 transition-colors">
                      One-time payment
                    </button>
                  </div>

                  {/* Fine Print */}
                  <div className="mt-6 text-xs text-gray-500">
                    {showTrial && plan.plan_type.toLowerCase() === 'individual' && (
                      <p>Rs 0 for 1 month, then {formatPrice(plan.price)} per month after. Offer only available if you haven't tried Premium before. Terms apply.</p>
                    )}
                    {showTrial && plan.plan_type.toLowerCase() === 'student' && (
                      <p>Rs 0 for 1 month, then {formatPrice(plan.price)} per month after. Offer reserved for students enrolled in an eligible accredited institution of higher education. Not available to users who have already tried Premium. Subject to the Spotify student discount Terms and Conditions.</p>
                    )}
                    {plan.plan_type.toLowerCase() === 'duo' && (
                      <p>For couples who reside at the same address. Terms apply.</p>
                    )}
                    {plan.plan_type.toLowerCase() === 'family' && (
                      <p>For up to 6 family members residing at the same address. Terms apply.</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
