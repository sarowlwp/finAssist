'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MarkdownRenderer from '@/components/MarkdownRenderer'

interface AgentReportCardProps {
  title: string
  emoji: string
  content: string
  defaultCollapsed?: boolean
}

const AgentReportCard: React.FC<AgentReportCardProps> = ({
  title,
  emoji,
  content,
  defaultCollapsed = false
}) => {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed)

  return (
    <Card className="mb-4" data-testid="agent-report">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors py-3 px-4"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2 text-base">
            <span>{emoji}</span>
            {title}
          </CardTitle>
          <span className="text-gray-400 text-sm">
            {collapsed ? '▼' : '▲'}
          </span>
        </div>
      </CardHeader>
      {!collapsed && (
        <CardContent className="pt-0 px-4 pb-4">
          <MarkdownRenderer content={content} />
        </CardContent>
      )}
    </Card>
  )
}

export default AgentReportCard
