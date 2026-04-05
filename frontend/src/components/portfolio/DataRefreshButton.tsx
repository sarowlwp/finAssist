import React from "react";
import { RefreshCw } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";

interface DataRefreshButtonProps extends ButtonProps {
  onClick: () => void;
  isLoading: boolean;
  className?: string;
}

const DataRefreshButton: React.FC<DataRefreshButtonProps> = ({
  onClick,
  isLoading,
  className,
  size = "sm",
  variant = "outline",
  ...props
}) => {
  return (
    <Button
      onClick={onClick}
      disabled={isLoading}
      size={size}
      variant={variant}
      className={className}
      {...props}
    >
      <RefreshCw
        className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
        aria-hidden="true"
      />
      {isLoading ? "刷新中..." : "刷新数据"}
    </Button>
  );
};

export default DataRefreshButton;
