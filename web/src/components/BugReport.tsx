'use client';

import { useState } from 'react';
import { Bug, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function BugReport() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    steps: '',
    expected: '',
    honeypot: '',
  });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setErrorMessage('');

    try {
      const res = await fetch('/api/bug-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to submit bug report');
      }

      setStatus('success');
      setFormData({ title: '', description: '', steps: '', expected: '', honeypot: '' });
    } catch (err) {
      setStatus('error');
      setErrorMessage(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  const inputClasses =
    'w-full bg-warm-white border border-sand rounded-xl px-4 py-3 text-espresso placeholder:text-bronze/40 focus:outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold transition-colors text-sm';

  return (
    <section id="bug-report" className="py-20 md:py-28 bg-warm-white">
      <div className="mx-auto max-w-2xl px-6">
        <div className="text-center mb-12">
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso">
            Report a Bug
          </h2>
          <p className="mt-4 text-lg text-bronze">
            Found something broken? Let us know and we&apos;ll fix it.
          </p>
        </div>

        {status === 'success' ? (
          <div className="bg-cream rounded-2xl border border-green-accent/30 p-8 text-center">
            <CheckCircle size={48} className="text-green-accent mx-auto mb-4" />
            <h3 className="font-semibold text-xl text-espresso mb-2">Bug Report Submitted</h3>
            <p className="text-bronze">
              Thanks for helping improve Golf Cam Replay! A GitHub issue has been created and
              we&apos;ll look into it.
            </p>
            <button
              onClick={() => setStatus('idle')}
              className="mt-6 text-sm text-gold hover:text-espresso transition-colors font-medium"
            >
              Submit another report
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Honeypot */}
            <input
              type="text"
              name="website"
              value={formData.honeypot}
              onChange={(e) => setFormData({ ...formData, honeypot: e.target.value })}
              className="absolute opacity-0 pointer-events-none"
              tabIndex={-1}
              autoComplete="off"
              aria-hidden="true"
            />

            <div>
              <label htmlFor="bug-title" className="block text-sm font-medium text-espresso mb-2">
                Title <span className="text-red-400">*</span>
              </label>
              <input
                id="bug-title"
                type="text"
                required
                placeholder="Brief description of the issue"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="bug-description" className="block text-sm font-medium text-espresso mb-2">
                Description <span className="text-red-400">*</span>
              </label>
              <textarea
                id="bug-description"
                required
                rows={4}
                placeholder="What happened? What were you doing when the bug occurred?"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="bug-steps" className="block text-sm font-medium text-espresso mb-2">
                Steps to Reproduce
              </label>
              <textarea
                id="bug-steps"
                rows={3}
                placeholder="1. Open the app&#10;2. Click on...&#10;3. Observe..."
                value={formData.steps}
                onChange={(e) => setFormData({ ...formData, steps: e.target.value })}
                className={inputClasses}
              />
            </div>

            <div>
              <label htmlFor="bug-expected" className="block text-sm font-medium text-espresso mb-2">
                Expected Behavior
              </label>
              <textarea
                id="bug-expected"
                rows={2}
                placeholder="What did you expect to happen instead?"
                value={formData.expected}
                onChange={(e) => setFormData({ ...formData, expected: e.target.value })}
                className={inputClasses}
              />
            </div>

            {status === 'error' && (
              <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
                <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{errorMessage}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="inline-flex items-center gap-2 bg-espresso hover:bg-charcoal text-white font-semibold px-6 py-3 rounded transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {status === 'loading' ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Bug size={18} />
                  Submit Bug Report
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
