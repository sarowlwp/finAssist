import React, { useState, useContext, createContext, ReactNode } from 'react';

interface TabsProps {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  children: ReactNode;
  className?: string;
}

interface TabProps {
  value: string;
  children: ReactNode;
  className?: string;
}

interface TabListProps {
  children: ReactNode;
  className?: string;
}

interface TabTriggerProps {
  value: string;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
}

interface TabContentProps {
  value: string;
  children: ReactNode;
  className?: string;
}

// 上下文类型
interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

// 创建上下文
const TabsContext = createContext<TabsContextValue | undefined>(undefined);

// 主容器组件
export const Tabs: React.FC<TabsProps> = ({
  defaultValue,
  value: controlledValue,
  onValueChange,
  children,
  className = '',
}) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '');

  const isControlled = controlledValue !== undefined;
  const currentValue = isControlled ? controlledValue : internalValue;

  const handleValueChange = (newValue: string) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }
    if (onValueChange) {
      onValueChange(newValue);
    }
  };

  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      <div className={className}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

// Tab 列表组件
export const TabList: React.FC<TabListProps> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`flex border-b dark:border-gray-700 mb-4 ${className}`}>
      {children}
    </div>
  );
};

// Tab 触发器组件
export const TabTrigger: React.FC<TabTriggerProps> = ({
  value,
  children,
  className = '',
  disabled = false,
}) => {
  const context = useContext(TabsContext);

  if (!context) {
    throw new Error('TabTrigger must be used within a Tabs component');
  }

  const isActive = context.value === value;

  const handleClick = () => {
    if (!disabled) {
      context.onValueChange(value);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`
        px-4 py-2 text-sm font-medium transition-colors
        ${isActive
          ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400'
        }
        ${disabled ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      {children}
    </button>
  );
};

// Tab 内容组件
export const TabContent: React.FC<TabContentProps> = ({
  value,
  children,
  className = '',
}) => {
  const context = useContext(TabsContext);

  if (!context) {
    throw new Error('TabContent must be used within a Tabs component');
  }

  const isActive = context.value === value;

  return (
    <div
      className={`${isActive ? 'block' : 'hidden'} ${className}`}
      role="tabpanel"
      aria-hidden={!isActive}
    >
      {children}
    </div>
  );
};

// 简单的使用示例组件
export const TabsExample: React.FC = () => {
  return (
    <Tabs defaultValue="tab1">
      <TabList>
        <TabTrigger value="tab1">Tab 1</TabTrigger>
        <TabTrigger value="tab2">Tab 2</TabTrigger>
        <TabTrigger value="tab3">Tab 3</TabTrigger>
      </TabList>
      <TabContent value="tab1">
        <p>Content for Tab 1</p>
      </TabContent>
      <TabContent value="tab2">
        <p>Content for Tab 2</p>
      </TabContent>
      <TabContent value="tab3">
        <p>Content for Tab 3</p>
      </TabContent>
    </Tabs>
  );
};

export default Tabs;
