"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Lock, Activity, CheckCircle2 } from "lucide-react"

export default function BlockchainVotingApp() {
  // Basic state management
  const [voteA, setVoteA] = useState(0)
  const [voteB, setVoteB] = useState(0)
  const [tallyA, setTallyA] = useState(0)
  const [tallyB, setTallyB] = useState(0)
  const [broadcast, setBroadcast] = useState(true)
  const [isMining, setIsMining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [blocks, setBlocks] = useState([{ id: 0, votes: { A: 0, B: 0 }, hash: "0000..." }])

  // Handle mining progress simulation
  useEffect(() => {
    let interval
    if (isMining) {
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsMining(false)
            return 0
          }
          return prev + 5
        })
      }, 100)
    }
    return () => clearInterval(interval)
  }, [isMining])

  // Handle vote submission
  const handleSubmit = () => {
    if (voteA === 0 && voteB === 0) return

    setIsMining(true)
    setProgress(0)

    // Simulate blockchain mining delay
    setTimeout(() => {
      if (broadcast) {
        // Update vote tallies
        setTallyA((prev) => prev + voteA)
        setTallyB((prev) => prev + voteB)

        // Add new block
        setBlocks((prev) => [
          ...prev,
          {
            id: prev.length,
            votes: { A: voteA, B: voteB },
            hash: `000${Math.random().toString(16).slice(2, 8)}...`,
          },
        ])
      }

      // Reset inputs
      setVoteA(0)
      setVoteB(0)
    }, 2000)
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Lock className="h-5 w-5 mr-2 text-emerald-400" />
            <h1 className="text-xl font-bold">BlockVote</h1>
          </div>
          <Badge variant="outline" className="bg-gray-800 text-emerald-400 border-emerald-400">
            <Activity className="h-3 w-3 mr-1" />
            Network Active
          </Badge>
        </div>

        {/* Main Card */}
        <Card className="bg-gray-800 border-gray-700 shadow-xl">
          <CardHeader className="border-b border-gray-700">
            <CardTitle className="text-2xl text-center text-emerald-400">Blockchain Voting Application</CardTitle>
            <CardDescription className="text-center text-gray-400">
              Cast your vote securely on the blockchain
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6 space-y-6">
            {/* Vote Form */}
            <div className="space-y-4">
              <div>
                <label htmlFor="voteA" className="block text-sm font-medium text-gray-300 mb-1">
                  Votes for Party A
                </label>
                <Input
                  id="voteA"
                  type="number"
                  min="0"
                  value={voteA}
                  onChange={(e) => setVoteA(Number.parseInt(e.target.value) || 0)}
                  className="bg-gray-900 border-gray-700 text-white"
                  disabled={isMining}
                />
              </div>

              <div>
                <label htmlFor="voteB" className="block text-sm font-medium text-gray-300 mb-1">
                  Votes for Party B
                </label>
                <Input
                  id="voteB"
                  type="number"
                  min="0"
                  value={voteB}
                  onChange={(e) => setVoteB(Number.parseInt(e.target.value) || 0)}
                  className="bg-gray-900 border-gray-700 text-white"
                  disabled={isMining}
                />
              </div>

              <Button
                onClick={handleSubmit}
                disabled={isMining || (voteA === 0 && voteB === 0)}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                {isMining ? "Mining Block..." : "Submit Vote"}
              </Button>
            </div>

            {/* Mining Progress */}
            {isMining && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Mining block</span>
                  <span className="text-emerald-400">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2 bg-gray-700" />
              </div>
            )}

            {/* Vote Tally */}
            <div className="bg-gray-900 p-4 rounded-lg">
              <h2 className="text-lg font-medium mb-4 text-center text-gray-300">Current Vote Tally</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg text-center">
                  <div className="text-lg text-gray-400">Party A</div>
                  <div className="text-4xl font-bold text-emerald-400">{tallyA}</div>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg text-center">
                  <div className="text-lg text-gray-400">Party B</div>
                  <div className="text-4xl font-bold text-emerald-400">{tallyB}</div>
                </div>
              </div>
            </div>

            {/* Recent Blocks */}
            <div className="bg-gray-900 p-4 rounded-lg">
              <h3 className="text-sm font-medium mb-2 text-gray-300">Recent Blocks</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {blocks
                  .slice()
                  .reverse()
                  .map((block) => (
                    <div key={block.id} className="bg-gray-800 p-2 rounded text-xs flex justify-between">
                      <span className="text-white">Block #{block.id}</span>
                      <span className="text-gray-400">
                        {block.id === 0 ? "Genesis Block" : `A: ${block.votes.A}, B: ${block.votes.B}`}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Broadcast Toggle */}
            <div className="flex items-center space-x-3 border border-gray-700 p-4 rounded-md bg-gray-900">
              <Checkbox
                id="broadcast"
                checked={broadcast}
                onCheckedChange={(checked) => setBroadcast(checked as boolean)}
                className="border-gray-600 data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500"
              />
              <div>
                <label htmlFor="broadcast" className="text-sm font-medium text-gray-300">
                  Broadcast votes to blockchain
                </label>
                <p className="text-xs text-gray-500">Uncheck to demo fork functionality</p>
              </div>
            </div>
          </CardContent>

          <CardFooter className="border-t border-gray-700 flex justify-between text-xs text-gray-500 pt-4">
            <div className="flex items-center">
              <span>{blocks.length} blocks</span>
            </div>
            <div className="flex items-center">
              <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-400" />
              <span>Secure Voting</span>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
