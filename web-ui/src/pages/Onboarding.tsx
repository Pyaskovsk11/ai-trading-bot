import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface OnboardingStep {
	step: string;
	completed: boolean;
	data: Record<string, any>;
}

interface OnboardingState {
	user_id: string;
	steps: OnboardingStep[];
	current_step: number;
	completed: boolean;
}

interface StepInfo {
	title: string;
	description: string;
	instructions: string[];
	fields: Array<{
		name: string;
		type: string;
		label: string;
		required?: boolean;
		options?: string[];
	}>;
}

const Onboarding: React.FC = () => {
	const [state, setState] = useState<OnboardingState | null>(null);
	const [currentStepInfo, setCurrentStepInfo] = useState<StepInfo | null>(null);
	const [formData, setFormData] = useState<Record<string, any>>({});
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [submitting, setSubmitting] = useState(false);
	const [integrationStatus, setIntegrationStatus] = useState<string | null>(null);
	
	const navigate = useNavigate();
	const userId = 'default_user'; // В реальном приложении получать из auth

	useEffect(() => {
		loadOnboardingState();
	}, []);

	useEffect(() => {
		if (state && state.current_step < state.steps.length) {
			loadStepInfo(state.steps[state.current_step].step);
		}
	}, [state]);

	const loadOnboardingState = async () => {
		try {
			const response = await fetch(`/api/v1/onboarding/state/${userId}`);
			if (!response.ok) throw new Error('Failed to load onboarding state');
			const data = await response.json();
			setState(data);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unknown error');
		} finally {
			setLoading(false);
		}
	};

	const loadStepInfo = async (stepName: string) => {
		try {
			const response = await fetch(`/api/v1/onboarding/steps/${stepName}`);
			if (!response.ok) throw new Error('Failed to load step info');
			const data = await response.json();
			setCurrentStepInfo(data);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unknown error');
		}
	};

	const handleInputChange = (fieldName: string, value: any) => {
		setFormData(prev => ({ ...prev, [fieldName]: value }));
	};

	const handleNext = async () => {
		if (!state || !currentStepInfo) return;

		setSubmitting(true);
		setIntegrationStatus('Интеграция с сервисами...');

		try {
			const response = await fetch(`/api/v1/onboarding/step/${userId}/${state.steps[state.current_step].step}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(formData)
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to complete step');
			}
			
			setIntegrationStatus('Интеграция успешна!');
			
			// Небольшая задержка для показа статуса
			await new Promise(resolve => setTimeout(resolve, 1000));
			
			const updatedState = await response.json();
			setState(updatedState);
			setFormData({});
			setIntegrationStatus(null);

			// Если онбординг завершен, переходим на дашборд
			if (updatedState.completed) {
				setIntegrationStatus('Перенаправление на дашборд...');
				await new Promise(resolve => setTimeout(resolve, 1500));
				navigate('/dashboard');
			}
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unknown error');
			setIntegrationStatus('Ошибка интеграции');
		} finally {
			setSubmitting(false);
		}
	};

	const handleSkip = () => {
		if (!state) return;
		// Переходим к следующему шагу без сохранения данных
		setState(prev => prev ? {
			...prev,
			current_step: prev.current_step + 1
		} : null);
		setFormData({});
	};

	const getStepIcon = (stepName: string) => {
		switch (stepName) {
			case 'telegram_link':
				return '📱';
			case 'api_keys':
				return '🔑';
			case 'trading_mode':
				return '⚙️';
			case 'strategy_selection':
				return '📈';
			case 'notifications':
				return '🔔';
			default:
				return '📋';
		}
	};

	const getStepColor = (stepName: string) => {
		switch (stepName) {
			case 'telegram_link':
				return 'bg-blue-500';
			case 'api_keys':
				return 'bg-green-500';
			case 'trading_mode':
				return 'bg-purple-500';
			case 'strategy_selection':
				return 'bg-orange-500';
			case 'notifications':
				return 'bg-red-500';
			default:
				return 'bg-gray-500';
		}
	};

	const renderField = (field: any) => {
		switch (field.type) {
			case 'text':
			case 'password':
				return (
					<input
						type={field.type}
						className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
						placeholder={field.label}
						value={formData[field.name] || ''}
						onChange={(e) => handleInputChange(field.name, e.target.value)}
						required={field.required}
					/>
				);
			case 'select':
				return (
					<select
						className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
						value={formData[field.name] || ''}
						onChange={(e) => handleInputChange(field.name, e.target.value)}
						required={field.required}
					>
						<option value="">Выберите...</option>
						{field.options?.map((option: string) => (
							<option key={option} value={option}>{option}</option>
						))}
					</select>
				);
			case 'number':
				return (
					<input
						type="number"
						className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
						placeholder={field.label}
						value={formData[field.name] || ''}
						onChange={(e) => handleInputChange(field.name, parseFloat(e.target.value))}
						required={field.required}
					/>
				);
			case 'checkbox':
				return (
					<label className="flex items-center space-x-3 p-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 cursor-pointer">
						<input
							type="checkbox"
							className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
							checked={formData[field.name] || false}
							onChange={(e) => handleInputChange(field.name, e.target.checked)}
						/>
						<span className="text-gray-700">{field.label}</span>
					</label>
				);
			default:
				return null;
		}
	};

	if (loading) {
		return (
			<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
				<div className="text-center">
					<div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
					<p className="text-lg text-gray-700 font-medium">Загрузка онбординга...</p>
					<p className="text-sm text-gray-500 mt-2">Подготовка системы</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-pink-100">
				<div className="text-center max-w-md mx-auto p-6">
					<div className="text-red-500 text-6xl mb-4">⚠️</div>
					<h2 className="text-xl font-bold text-gray-900 mb-2">Произошла ошибка</h2>
					<p className="text-red-600 mb-6">{error}</p>
					<button
						onClick={loadOnboardingState}
						className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 font-medium"
					>
						Попробовать снова
					</button>
				</div>
			</div>
		);
	}

	if (!state || !currentStepInfo) {
		return (
			<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
				<div className="text-center">
					<div className="text-gray-400 text-6xl mb-4">📋</div>
					<p className="text-lg text-gray-600">Нет данных для отображения</p>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-8">
			<div className="max-w-4xl mx-auto px-4">
				{/* Header */}
				<div className="text-center mb-8">
					<h1 className="text-3xl font-bold text-gray-900 mb-2">Добро пожаловать в AI Trading Bot</h1>
					<p className="text-gray-600">Настройте систему за несколько простых шагов</p>
				</div>

				{/* Progress Bar */}
				<div className="mb-8">
					<div className="flex justify-between items-center mb-3">
						<span className="text-sm font-medium text-gray-700">
							Шаг {state.current_step + 1} из {state.steps.length}
						</span>
						<span className="text-sm font-medium text-blue-600">
							{Math.round(((state.current_step + 1) / state.steps.length) * 100)}%
						</span>
					</div>
					<div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
						<div
							className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-500 ease-out"
							style={{ width: `${((state.current_step + 1) / state.steps.length) * 100}%` }}
						></div>
					</div>
				</div>

				{/* Steps Overview */}
				<div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
					{state.steps.map((step, index) => (
						<div
							key={step.step}
							className={`flex flex-col items-center p-4 rounded-lg transition-all duration-300 ${
								index < state.current_step
									? 'bg-green-100 border-2 border-green-300'
									: index === state.current_step
									? 'bg-blue-100 border-2 border-blue-300 shadow-lg'
									: 'bg-gray-100 border-2 border-gray-200'
							}`}
						>
							<div className={`text-2xl mb-2 ${index < state.current_step ? 'animate-bounce' : ''}`}>
								{getStepIcon(step.step)}
							</div>
							<div className="text-xs text-center font-medium">
								{step.step.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
							</div>
							{step.completed && (
								<div className="mt-2 text-green-600 text-lg">✅</div>
							)}
						</div>
					))}
				</div>

				{/* Step Content */}
				<div className="bg-white rounded-xl shadow-xl p-8 border border-gray-100">
					{/* Step Header */}
					<div className="flex items-center mb-6">
						<div className={`w-12 h-12 rounded-full ${getStepColor(state.steps[state.current_step].step)} flex items-center justify-center text-white text-xl mr-4`}>
							{getStepIcon(state.steps[state.current_step].step)}
						</div>
						<div>
							<h1 className="text-2xl font-bold text-gray-900">
								{currentStepInfo.title}
							</h1>
							<p className="text-gray-600">
								{currentStepInfo.description}
							</p>
						</div>
					</div>

					{/* Instructions */}
					<div className="mb-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
						<h3 className="text-sm font-semibold text-blue-900 mb-3 flex items-center">
							📋 Инструкции:
						</h3>
						<ul className="space-y-2">
							{currentStepInfo.instructions.map((instruction, index) => (
								<li key={index} className="flex items-start">
									<span className="text-blue-600 mr-2 mt-1">•</span>
									<span className="text-sm text-blue-800">{instruction}</span>
								</li>
							))}
						</ul>
					</div>

					{/* Form */}
					<div className="space-y-6">
						{currentStepInfo.fields.map((field) => (
							<div key={field.name} className="space-y-2">
								<label className="block text-sm font-semibold text-gray-700">
									{field.label}
									{field.required && <span className="text-red-500 ml-1">*</span>}
								</label>
								{renderField(field)}
							</div>
						))}
					</div>

					{/* Integration Status */}
					{integrationStatus && (
						<div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
							<div className="flex items-center">
								<div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent mr-3"></div>
								<span className="text-sm text-blue-800 font-medium">{integrationStatus}</span>
							</div>
						</div>
					)}

					{/* Actions */}
					<div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
						<button
							onClick={handleSkip}
							className="px-6 py-3 text-gray-600 hover:text-gray-800 font-medium transition-all duration-200"
						>
							Пропустить
						</button>
						<button
							onClick={handleNext}
							disabled={submitting || !formData || Object.keys(formData).length === 0}
							className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
						>
							{submitting ? (
								<div className="flex items-center">
									<div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
									Обработка...
								</div>
							) : (
								state.current_step + 1 >= state.steps.length ? 'Завершить настройку' : 'Продолжить'
							)}
						</button>
					</div>
				</div>

				{/* Footer */}
				<div className="text-center mt-8">
					<p className="text-sm text-gray-500">
						Все данные защищены и используются только для работы системы
					</p>
				</div>
			</div>
		</div>
	);
};

export default Onboarding;
