# Промпт для AI-агента Cursor: Создание легковесного веб-приложения для AI трейдинг-бота

## Задача

Создать простое и легковесное веб-приложение для AI трейдинг-бота, которое будет работать локально на ноутбуке без создания значительной нагрузки. Приложение должно отображать торговые сигналы, базовую статистику и простые графики.

## Технический стек

- **Фронтенд**: React с TypeScript (используя create_react_app)
- **Стилизация**: Tailwind CSS для легкого и эффективного стилизования
- **Графики**: Recharts (легковесная библиотека для React)
- **Состояние**: Используйте React Context API вместо тяжелых решений для управления состоянием
- **Данные**: Загрузка из локальных JSON-файлов или простого API

## Структура приложения

### 1. Компоненты

Создайте следующие основные компоненты:

- **Header**: Простой заголовок с названием приложения
- **Dashboard**: Главная страница с обзором ключевых метрик
- **SignalsList**: Компонент для отображения списка сигналов
- **SignalDetail**: Компонент для просмотра деталей сигнала
- **SimpleChart**: Компонент для отображения графиков цен и индикаторов
- **Footer**: Простой футер с информацией

### 2. Страницы

Создайте следующие страницы:

- **Home**: Главная страница с дашбордом
- **Signals**: Страница со списком сигналов
- **SignalView**: Страница для просмотра деталей конкретного сигнала

### 3. Маршрутизация

Используйте React Router для навигации между страницами:

```tsx
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/signals" element={<Signals />} />
  <Route path="/signals/:id" element={<SignalView />} />
</Routes>
```

## Функциональность

### 1. Дашборд (Home)

Создайте простой дашборд, который отображает:

- Количество активных сигналов
- Распределение сигналов по типам (BUY, SELL, HOLD)
- Успешность сигналов (простая статистика)
- График с общей динамикой цен основных активов (BTC/ETH)

### 2. Список сигналов (Signals)

Создайте страницу со списком сигналов, которая отображает:

- Таблицу с основной информацией о сигналах (актив, тип, уверенность, цена, время)
- Фильтрацию по типу сигнала и активу
- Сортировку по времени создания и уверенности
- Пагинацию для эффективной работы с большим количеством сигналов

### 3. Детали сигнала (SignalView)

Создайте страницу с деталями сигнала, которая отображает:

- Всю информацию о сигнале (актив, тип, уверенность, цена, целевая цена, стоп-лосс)
- Простой график цены с отмеченными уровнями входа, целевой ценой и стоп-лоссом
- XAI-объяснение сигнала в текстовом виде
- Технические индикаторы, использованные для генерации сигнала

## Данные

Для упрощения работы с данными:

1. Создайте моковые данные в JSON-файлах:
   - `signals.json`: Список сигналов
   - `prices.json`: Исторические цены для графиков
   - `stats.json`: Статистика для дашборда

2. Используйте простые функции для загрузки данных:

```tsx
const fetchSignals = async () => {
  // В реальном приложении здесь был бы API-запрос
  const response = await fetch('/data/signals.json');
  return response.json();
};
```

## Оптимизация производительности

Для обеспечения легковесности приложения:

1. Используйте React.memo для предотвращения ненужных ререндеров компонентов
2. Применяйте ленивую загрузку для компонентов страниц:

```tsx
const SignalView = React.lazy(() => import('./pages/SignalView'));
```

3. Оптимизируйте размер бандла:
   - Используйте только необходимые компоненты из библиотек
   - Избегайте тяжелых зависимостей

4. Используйте виртуализацию для длинных списков:

```tsx
import { FixedSizeList } from 'react-window';

const VirtualizedSignalsList = ({ signals }) => (
  <FixedSizeList
    height={500}
    width="100%"
    itemCount={signals.length}
    itemSize={50}
  >
    {({ index, style }) => (
      <div style={style}>
        <SignalItem signal={signals[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

## Пример структуры проекта

```
src/
├── components/
│   ├── Header.tsx
│   ├── Footer.tsx
│   ├── Dashboard/
│   │   ├── StatCard.tsx
│   │   ├── SignalTypeDistribution.tsx
│   │   └── SuccessRateChart.tsx
│   ├── Signals/
│   │   ├── SignalsList.tsx
│   │   ├── SignalItem.tsx
│   │   └── SignalFilter.tsx
│   └── Charts/
│       ├── PriceChart.tsx
│       └── IndicatorChart.tsx
├── pages/
│   ├── Home.tsx
│   ├── Signals.tsx
│   └── SignalView.tsx
├── types/
│   ├── Signal.ts
│   ├── Price.ts
│   └── Stats.ts
├── utils/
│   ├── formatters.ts
│   └── dataFetchers.ts
├── data/
│   ├── signals.json
│   ├── prices.json
│   └── stats.json
├── App.tsx
└── index.tsx
```

## Пример компонента SignalItem

```tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { formatDate } from '../utils/formatters';
import { Signal } from '../types/Signal';

interface SignalItemProps {
  signal: Signal;
}

const SignalItem: React.FC<SignalItemProps> = React.memo(({ signal }) => {
  const getSignalTypeColor = (type: string) => {
    switch (type) {
      case 'BUY':
        return 'text-green-600';
      case 'SELL':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Link 
      to={`/signals/${signal.id}`}
      className="block p-4 border rounded-lg mb-2 hover:bg-gray-50 transition-colors"
    >
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-medium">{signal.asset_pair}</h3>
          <p className="text-sm text-gray-500">
            {formatDate(signal.created_at)}
          </p>
        </div>
        <div className="flex items-center">
          <span className={`font-bold ${getSignalTypeColor(signal.signal_type)}`}>
            {signal.signal_type}
          </span>
          <span className="ml-4 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
            {(signal.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="mt-2 text-sm">
        <span className="text-gray-600">Цена: </span>
        <span className="font-medium">${signal.price_at_signal.toFixed(2)}</span>
        {signal.target_price && (
          <>
            <span className="text-gray-600 ml-2">Цель: </span>
            <span className="font-medium">${signal.target_price.toFixed(2)}</span>
          </>
        )}
      </div>
    </Link>
  );
});

export default SignalItem;
```

## Пример простого графика цены

```tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import { Price } from '../types/Price';

interface PriceChartProps {
  prices: Price[];
  entryPrice?: number;
  targetPrice?: number;
  stopLoss?: number;
}

const PriceChart: React.FC<PriceChartProps> = ({ 
  prices, 
  entryPrice, 
  targetPrice, 
  stopLoss 
}) => {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={prices}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            }}
            minTickGap={50}
          />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
            formatter={(value) => [`$${value}`, 'Цена']}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" 
            dot={false} 
            strokeWidth={2}
          />
          {entryPrice && (
            <ReferenceLine 
              y={entryPrice} 
              stroke="#6366f1" 
              strokeDasharray="3 3" 
              label={{ value: 'Вход', position: 'insideTopRight' }}
            />
          )}
          {targetPrice && (
            <ReferenceLine 
              y={targetPrice} 
              stroke="#10b981" 
              strokeDasharray="3 3" 
              label={{ value: 'Цель', position: 'insideTopRight' }}
            />
          )}
          {stopLoss && (
            <ReferenceLine 
              y={stopLoss} 
              stroke="#ef4444" 
              strokeDasharray="3 3" 
              label={{ value: 'Стоп', position: 'insideBottomRight' }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceChart;
```

## Инструкции по реализации

1. Используйте команду `create_react_app` для создания нового проекта:
   ```bash
   create_react_app trading_bot_ui --template typescript
   cd trading_bot_ui
   ```

2. Установите необходимые зависимости:
   ```bash
   npm install react-router-dom recharts react-window tailwindcss
   ```

3. Настройте Tailwind CSS:
   ```bash
   npx tailwindcss init
   ```

4. Создайте структуру проекта и компоненты согласно приведенному выше плану

5. Создайте моковые данные в папке `public/data/`

6. Реализуйте базовую функциональность для отображения сигналов и графиков

7. Оптимизируйте производительность приложения

Пожалуйста, создайте легковесное веб-приложение для AI трейдинг-бота, которое будет работать локально на ноутбуке без создания значительной нагрузки.
