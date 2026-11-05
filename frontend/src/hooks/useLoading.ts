import { useState, useEffect, useCallback, useRef } from 'react';

interface UseLoadingOptions {
  // 是否在组件卸载时取消请求
  cancelOnUnmount?: boolean;
  // 延迟显示加载状态的时间（毫秒）
  delay?: number;
}

interface UseLoadingReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  setData: (data: T | null) => void;
  setError: (error: string | null) => void;
}

/**
 * 管理异步加载状态的自定义 Hook
 * 支持组件卸载时自动取消请求
 */
export function useLoading<T>(
  fetcher: () => Promise<T>,
  options: UseLoadingOptions = {}
): UseLoadingReturn<T> {
  const { cancelOnUnmount = true, delay = 0 } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const isMounted = useRef(true);
  const abortController = useRef<AbortController | null>(null);
  const showLoadingTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const execute = useCallback(async () => {
    // 重置状态
    if (!delay) {
      if (isMounted.current) {
        setIsLoading(true);
      }
    } else {
      // 延迟显示加载状态
      showLoadingTimeout.current = setTimeout(() => {
        if (isMounted.current) {
          setIsLoading(true);
        }
      }, delay);
    }

    // 创建新的 AbortController
    abortController.current = new AbortController();

    try {
      const result = await fetcher();
      
      if (isMounted.current) {
        setData(result);
        setError(null);
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // 请求被取消，不处理错误
        return;
      }
      
      if (isMounted.current) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setData(null);
      }
    } finally {
      if (showLoadingTimeout.current) {
        clearTimeout(showLoadingTimeout.current);
      }
      
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [fetcher, delay]);

  useEffect(() => {
    isMounted.current = true;
    execute();

    return () => {
      isMounted.current = false;
      
      // 取消未完成的请求
      if (cancelOnUnmount && abortController.current) {
        abortController.current.abort();
      }
      
      // 清除延迟定时器
      if (showLoadingTimeout.current) {
        clearTimeout(showLoadingTimeout.current);
      }
    };
  }, [execute, cancelOnUnmount]);

  return {
    data,
    isLoading,
    error,
    refetch: execute,
    setData,
    setError,
  };
}

/**
 * 简化的加载状态管理 Hook
 * 适用于不需要自动执行的场景
 */
export function useLoadingState(options: { initialLoading?: boolean } = {}) {
  const { initialLoading = false } = options;
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const safeSetLoading = useCallback((loading: boolean) => {
    if (isMounted.current) {
      setIsLoading(loading);
    }
  }, []);

  const safeSetError = useCallback((err: string | null) => {
    if (isMounted.current) {
      setError(err);
    }
  }, []);

  return {
    isLoading,
    error,
    setIsLoading: safeSetLoading,
    setError: safeSetError,
  };
}
