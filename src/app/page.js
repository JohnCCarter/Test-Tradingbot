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
      setBalance(data.balance || {});
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

  if (isLoading) return <div className="flex items-center justify-center min-h-screen">Laddar...</div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <main className="container mx-auto px-4 py-8">
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

        {showSettings && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">Bot Inställningar</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
                        value={settings[key] !== null && settings[key] !== undefined ? settings[key] : ''}
                        onChange={handleSettingsChange}
                        className="p-2 border rounded"
                      />
                    )}
                  </div>
                )
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleSaveSettings}
                className="px-6 py-2 rounded-lg font-semibold bg-green-500 hover:bg-green-600 text-white"
              >
                {isLoading ? 'Sparar...' : 'Spara Inställningar'}
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Totalt antal trades</h2>
            <p className="text-2xl">{metrics.total_trades}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Vinnande trades</h2>
            <p className="text-2xl text-green-600">{metrics.winning_trades}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Förlorande trades</h2>
            <p className="text-2xl text-red-600">{metrics.losing_trades}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Total PnL</h2>
            <p className="text-2xl">{typeof metrics.total_pnl === 'number' ? metrics.total_pnl.toFixed(2) : '0.00'}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-xl font-semibold mb-4">PnL Över Tid</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={pnlHistory}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(timestamp) => new Date(timestamp).toLocaleTimeString()} />
                <YAxis />
                <Tooltip formatter={(value) => value.toFixed(2)} labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()} />
                <Legend />
                <Line type="monotone" dataKey="pnl" stroke="#8884d8" activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-xl font-semibold mb-4">Konton</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {balance && Object.keys(balance).length > 0 && Object.entries(balance).map(([currency, amounts]) => (
              !['info', 'free', 'used', 'total'].includes(currency) && amounts && (
                <div key={currency} className="p-4 bg-gray-50 rounded">
                  <h3 className="font-medium text-gray-600">{currency}</h3>
                  <p className="text-lg">
                    <strong>Total:</strong> {typeof amounts.total === 'number' ? amounts.total.toFixed(8) : amounts.total},
                    <strong>Available:</strong> {typeof amounts.free === 'number' ? amounts.free.toFixed(8) : amounts.free}
                  </p>
                </div>
              )
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Senaste Trades</h2>
          {recentTrades.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Datum</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Typ</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pris</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Antal</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PnL</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentTrades.map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(trade.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.side}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.price ? parseFloat(trade.price).toFixed(8) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.amount ? parseFloat(trade.amount).toFixed(8) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.fee ? `${parseFloat(trade.fee.cost).toFixed(8)} ${trade.fee.currency}` : 'N/A'}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                        trade.pnl > 0 ? 'text-green-600' : trade.pnl < 0 ? 'text-red-600' : 'text-gray-500'
                      }`}>
                        {typeof trade.pnl === 'number' ? trade.pnl.toFixed(2) : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">Inga senaste trades att visa.</p>
          )}
        </div>

        {/* Trading Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Manual Trading</h2>
          <div className="space-y-4">
            <div className="flex space-x-4">
              <button
                onClick={() => setTradeType('buy')}
                className={`px-4 py-2 rounded ${
                  tradeType === 'buy' ? 'bg-green-500 text-white' : 'bg-gray-200'
                }`}
              >
                Buy
              </button>
              <button
                onClick={() => setTradeType('sell')}
                className={`px-4 py-2 rounded ${
                  tradeType === 'sell' ? 'bg-red-500 text-white' : 'bg-gray-200'
                }`}
              >
                Sell
              </button>
            </div>
            
            <div className="flex space-x-4">
              <input
                type="number"
                value={tradeAmount}
                onChange={(e) => setTradeAmount(e.target.value)}
                placeholder="Amount"
                className="border rounded px-3 py-2 flex-1"
              />
              <button
                onClick={handleTrade}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Execute Trade
              </button>
            </div>
            
            {tradeStatus && (
              <div className={`p-3 rounded ${
                tradeStatus.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {tradeStatus}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
} 