import React, { useEffect, useState } from 'react'
import { analysisApi } from '../../api/api'

const TextQualityAnalysis = ({ topicId, topicTitle }) => {
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        setLoading(true)
        const data = await analysisApi.getTextQuality(topicId)
        setAnalyses(data || [])
      } catch (err) {
        setError(err.message || 'Tahlilni yuklashda xato')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    if (topicId) {
      fetchAnalyses()
    }
  }, [topicId])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        {error}
      </div>
    )
  }

  if (!analyses || analyses.length === 0) {
    return (
      <div className="p-8 text-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-600">Hali tahlil mavjud emas</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Matn Sifati Tahlili</h2>
        <p className="text-gray-600 mb-6">Mavzu: <span className="font-semibold">{topicTitle}</span></p>
      </div>

      {analyses.map((analysis) => {
        let result = {}
        try {
          result = typeof analysis.result === 'string' ? JSON.parse(analysis.result) : analysis.result
        } catch (e) {
          result = {}
        }

        const qualityScore = analysis.score || result.quality_score || 0
        const wordCount = result.word_count || 0
        const uniqueWords = result.unique_words || 0
        const sentenceCount = result.sentence_count || 0
        const paragraphCount = result.paragraph_count || 0
        const avgWPS = result.avg_words_per_sentence || 0
        const vocabRichness = result.vocab_richness || 0

        const getScoreColor = (score) => {
          if (score >= 80) return 'text-green-600'
          if (score >= 60) return 'text-yellow-600'
          return 'text-red-600'
        }

        const getScoreBg = (score) => {
          if (score >= 80) return 'bg-green-50'
          if (score >= 60) return 'bg-yellow-50'
          return 'bg-red-50'
        }

        return (
          <div key={analysis.id} className={`p-6 border border-gray-200 rounded-lg ${getScoreBg(qualityScore)}`}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Umumiy Ko'rsatkichlar</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-700">So'zlar soni:</span>
                    <span className="font-semibold text-gray-900">{wordCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Noyob so'zlar:</span>
                    <span className="font-semibold text-gray-900">{uniqueWords}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Gap soni:</span>
                    <span className="font-semibold text-gray-900">{sentenceCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Paragraf soni:</span>
                    <span className="font-semibold text-gray-900">{paragraphCount}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Tahlil Ko'rsatkichlari</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-700">O'rtacha gap uzunligi:</span>
                    <span className="font-semibold text-gray-900">{avgWPS} so'z</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Lug'at boyligi:</span>
                    <span className="font-semibold text-gray-900">{vocabRichness}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-t border-gray-200 mt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-2">Umumiy Sifat Ballari</p>
                  <p className={`text-3xl font-bold ${getScoreColor(qualityScore)}`}>
                    {qualityScore.toFixed(1)} / 100
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 mb-2">
                    {new Date(analysis.created_at).toLocaleDateString('uz-UZ', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                  <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    qualityScore >= 80 ? 'bg-green-100 text-green-800' :
                    qualityScore >= 60 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {qualityScore >= 80 ? '✅ Yaxshi' :
                     qualityScore >= 60 ? '⚠️ O\'rtacha' :
                     '❌ Yomon'}
                  </div>
                </div>
              </div>
            </div>

            {result.summary && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">{result.summary}</p>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default TextQualityAnalysis
