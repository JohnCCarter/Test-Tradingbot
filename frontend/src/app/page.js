'use client';

import { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import React from 'react';

export default function Dashboard({ params, searchParams }) {
  React.use(params);
  React.use(searchParams);

  const [metrics, setMetrics] = useState({
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    total_pnl: 0,
    win_rate: 0
  });
  const [balance, setBalance] = useState({});
  const [recentTrades, setRecentTrades] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const [settings, setSettings] = useState({
    RSI_PERIOD: '',
    RSI_OVERBOUGHT: '',
    RSI_OVERSOLD: '',
    STOP_LOSS_PERCENT: '',
    TAKE_PROFIT_PERCENT: '',
    MAX_TRADES: '',
    TRADE_AMOUNT_USD: '',
    COOLOFF_PERIOD_SECONDS: '',
    EMA_SHORT_PERIOD: '',
    EMA_LONG_PERIOD: '',
    TREND_EMA_PERIOD: '',
    MIN_VOLUME: '',
    TRADE_TIME_START: '',
    TRADE_TIME_END: '',
    TIMEZONE: '',
    RISK_PER_TRADE_PERCENT: '',
    MAX_TOTAL_RISK_PERCENT: '',
    MODE: '',
    DRY_RUN: false,
    CURRENCY_PAIR: '',
    TIME_INTERVAL: '',
    EMAIL_NOTIFICATIONS: false,
    EMAIL_SENDER: '',
    EMAIL_RECEIVER: '',
    EMAIL_PASSWORD: '',
    SL_WINDOW_MULTIPLIER: '',
    TP_WINDOW_MULTIPLIER: '',
  });

  const [pnlHistory, setPnlHistory] = useState([]);
  const [tradeAmount, setTradeAmount] = useState('');
  const [tradeType, setTradeType] = useState('buy');
  const [tradeStatus, setTradeStatus] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [priceHistory, setPriceHistory] = useState([]);
  const [priceAlerts, setPriceAlerts] = useState([]);
  const [alertPrice, setAlertPrice] = useState('');
  const [alertType, setAlertType] = useState('above');

  // Add price fetching
  const fetchPrice = useCallback(async () => {
    try {
      const response = await fetch('/api/price');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (currentPrice) {
        const change = ((data.price - currentPrice) / currentPrice) * 100;
        setPriceChange(change);
      }
      setCurrentPrice(data.price);
      if (data.alerts && data.alerts.length > 0) {
        setPriceAlerts(prev => [...prev, ...data.alerts]);
      }
    } catch (error) {
      console.error('Error fetching price:', error);
    }
  }, [currentPrice]);

  // Add price history fetching
  const fetchPriceHistory = useCallback(async () => {
    try {
      const response = await fetch('/api/price/history');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPriceHistory(data);
    } catch (error) {
      console.error('Error fetching price history:', error);
    }
  }, []);

  useEffect(() => {
    fetchPrice();
    fetchPriceHistory();
    const priceInterval = setInterval(fetchPrice, 1000);
    const historyInterval = setInterval(fetchPriceHistory, 5000);
    return () => {
      clearInterval(priceInterval);
      clearInterval(historyInterval);
    };
  }, [fetchPrice, fetchPriceHistory]);

  // Quick amount buttons
  const quickAmounts = [0.001, 0.01, 0.1, 1];

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch('/api/settings');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSettings(data);
        console.log('Settings fetched:', data);
      } catch (error) {
        console.error('Error fetching settings:', error);
        setError(`Kunde inte hämta inställningar: ${error.message}`);
      }
    };

    fetchSettings();
  }, []);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/metrics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMetrics(data.metrics || { total_trades: 0, winning_trades: 0, losing_trades: 0, total_pnl: 0, win_rate: 0 });
      
      // Ensure balance values are numbers
      const processedBalance = {};
      if (data.balance && data.balance.total) {
        Object.entries(data.balance.total).forEach(([currency, amount]) => {
          processedBalance[currency] = parseFloat(amount) || 0;
        });
      }
      setBalance(processedBalance);
      
      setRecentTrades(data.trade_history || []);
      setPnlHistory(data.pnl_history || []);
      setIsRunning(data.is_running);
      setIsLoading(false);
      console.log('Metrics fetched:', data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setError(`Kunde inte hämta data: ${error.message}`);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const intervalId = setInterval(fetchMetrics, 5000);

    return () => clearInterval(intervalId);
  }, [fetchMetrics]);

  const handleToggleBot = async () => {
    setIsLoading(true);
    setError(null);
    const action = isRunning ? 'stop' : 'start';
    try {
      const response = await fetch('/api/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setIsRunning(data.is_running);
      console.log(`Bot status toggled: ${data.is_running}`, data);
      fetchMetrics();
    } catch (error) {
      console.error('Error toggling bot:', error);
      setError(`Kunde inte ändra botens status: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prevSettings => ({
      ...prevSettings,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSaveSettings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const settingsToSave = { ...settings };
      
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settingsToSave),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Settings saved:', result);
      const updatedSettingsResponse = await fetch('/api/settings');
      if (!updatedSettingsResponse.ok) {
        throw new Error(`HTTP error! status: ${updatedSettingsResponse.status}`);
      }
      const updatedSettings = await updatedSettingsResponse.json();
      setSettings(updatedSettings);
    } catch (error) {
      console.error('Error saving settings:', error);
      setError(`Kunde inte spara inställningar: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrade = async () => {
    try {
      setTradeStatus('Processing trade...');
      const response = await fetch('http://localhost:5000/api/trade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: tradeType,
          amount: parseFloat(tradeAmount),
        }),
      });
      
      const data = await response.json();
      if (response.ok) {
        setTradeStatus(`Trade executed successfully: ${data.message}`);
        // Refresh metrics after trade
        fetchMetrics();
      } else {
        setTradeStatus(`Error: ${data.error}`);
      }
    } catch (error) {
      setTradeStatus(`Error: ${error.message}`);
    }
  };

  const handleAddAlert = async () => {
    try {
      const response = await fetch('/api/price/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: alertType,
          price: parseFloat(alertPrice)
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      setAlertPrice('');
      setAlertType('above');
    } catch (error) {
      console.error('Error adding price alert:', error);
    }
  };

  if (isLoading) return <div className="flex items-center justify-center min-h-screen">Laddar...</div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <main className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Trading Bot Dashboard</h1>
          <div className="flex gap-4">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="px-6 py-2 rounded-lg font-semibold bg-blue-500 hover:bg-blue-600 text-white"
            >
              {showSettings ? 'Stäng Inställningar' : 'Öppna Inställningar'}
            </button>
            <button
              onClick={handleToggleBot}
              className={`px-6 py-2 rounded-lg font-semibold ${
                isRunning 
                  ? 'bg-red-500 hover:bg-red-600 text-white' 
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isRunning ? 'Stoppa Bot' : 'Starta Bot'}
            </button>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Trading Status Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Trading Status</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">Status:</span>
                <span className={`font-semibold ${isRunning ? 'text-green-500' : 'text-red-500'}`}>
                  {isRunning ? 'Kör' : 'Stoppad'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Senaste Uppdatering:</span>
                <span>{new Date().toLocaleTimeString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Aktiva Trades:</span>
                <span>{recentTrades.length}</span>
              </div>
            </div>
          </div>

          {/* Live Price Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Live Pris</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">Nuvarande Pris:</span>
                <span className="text-2xl font-bold">
                  {currentPrice ? currentPrice.toFixed(2) : 'Laddar...'} USD
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">24h Förändring:</span>
                <span className={`font-semibold ${priceChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {priceChange.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Price Chart Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Prisutveckling</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(timestamp) => new Date(timestamp).toLocaleTimeString()}
                />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip 
                  labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                  formatter={(value) => [`${value.toFixed(2)} USD`, 'Pris']}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#2563eb" 
                  dot={false}
                  name="Pris"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Price Alerts Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Prisvarningar</h2>
          <div className="space-y-4">
            <div className="flex space-x-4">
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                className="border rounded px-3 py-2"
              >
                <option value="above">Över</option>
                <option value="below">Under</option>
              </select>
              <input
                type="number"
                value={alertPrice}
                onChange={(e) => setAlertPrice(e.target.value)}
                placeholder="Pris"
                className="border rounded px-3 py-2 flex-1"
              />
              <button
                onClick={handleAddAlert}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Lägg till Varning
              </button>
            </div>
            
            {priceAlerts.length > 0 && (
              <div className="space-y-2">
                {priceAlerts.map((alert, index) => (
                  <div 
                    key={index}
                    className="bg-yellow-100 text-yellow-800 p-3 rounded"
                  >
                    {alert}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Balance and Active Orders Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Balance Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Balans</h2>
            <div className="space-y-2">
              {Object.entries(balance).map(([currency, amount]) => (
                <div key={currency} className="flex justify-between">
                  <span className="font-medium">{currency}:</span>
                  <span>{typeof amount === 'number' ? amount.toFixed(8) : amount}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Orders Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Aktiva Ordrar</h2>
            <div className="space-y-2">
              {recentTrades.filter(trade => trade.status === 'active').map((trade, index) => (
                <div key={index} className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">{trade.type}</span>
                    <span className="text-sm text-gray-500 ml-2">{trade.amount}</span>
                  </div>
                  <span className={`font-semibold ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {trade.pnl.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Trades Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Senaste Trades</h2>
            <div className="space-y-2">
              {recentTrades.slice(0, 5).map((trade, index) => (
                <div key={index} className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">{trade.type}</span>
                    <span className="text-sm text-gray-500 ml-2">{trade.amount}</span>
                  </div>
                  <span className={`font-semibold ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {trade.pnl.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Trading Controls Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Settings Card */}
          {showSettings && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Bot Inställningar</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.keys(settings).map(key => (
                  !['API_KEY', 'API_SECRET', 'EMAIL_PASSWORD'].includes(key) && (
                    <div key={key} className="flex flex-col">
                      <label htmlFor={key} className="mb-1 font-medium">{key.replace(/_/g, ' ')}:</label>
                      {typeof settings[key] === 'boolean' ? (
                        <input
                          type="checkbox"
                          id={key}
                          name={key}
                          checked={settings[key]}
                          onChange={handleSettingsChange}
                          className="mt-1"
                        />
                      ) : (
                        <input
                          type="text"
                          id={key}
                          name={key}
                          value={settings[key]}
                          onChange={handleSettingsChange}
                          className="border rounded px-3 py-2 mt-1"
                        />
                      )}
                    </div>
                  )
                ))}
              </div>
              <button
                onClick={handleSaveSettings}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Spara Inställningar
              </button>
            </div>
          )}

          {/* Manual Trading Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Manuell Handel</h2>
            <div className="space-y-4">
              <div className="flex space-x-4">
                <button
                  onClick={() => setTradeType('buy')}
                  className={`px-4 py-2 rounded ${
                    tradeType === 'buy' ? 'bg-green-500 text-white' : 'bg-gray-200'
                  }`}
                >
                  Köp
                </button>
                <button
                  onClick={() => setTradeType('sell')}
                  className={`px-4 py-2 rounded ${
                    tradeType === 'sell' ? 'bg-red-500 text-white' : 'bg-gray-200'
                  }`}
                >
                  Sälj
                </button>
              </div>
              
              <div className="space-y-2">
                <div className="flex space-x-2">
                  {quickAmounts.map((amount) => (
                    <button
                      key={amount}
                      onClick={() => setTradeAmount(amount.toString())}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      {amount}
                    </button>
                  ))}
                </div>
                
                <div className="flex space-x-4">
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder="Belopp"
                    className="border rounded px-3 py-2 flex-1"
                  />
                  <button
                    onClick={handleTrade}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                  >
                    Utför Handel
                  </button>
                </div>
              </div>
              
              {tradeStatus && (
                <div className={`p-3 rounded ${
                  tradeStatus.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                }`}>
                  {tradeStatus}
                </div>
              )}

              {currentPrice && (
                <div className="text-sm text-gray-500">
                  Beräknat värde: {(parseFloat(tradeAmount || 0) * currentPrice).toFixed(2)} USD
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}