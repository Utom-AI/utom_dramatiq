import { useState, ChangeEvent } from 'react';
import { MantineProvider, Container, TextInput, Button, Text, Paper, Stack, Title, Progress, Alert } from '@mantine/core';
import axios from 'axios';

interface ActionPoint {
  action: string;
  context: string;
  priority: 'High' | 'Medium' | 'Low';
}

interface ProcessingResult {
  job_id: number;
  video_url: string;
  transcription: string;
  action_points: ActionPoint[];
  error?: string;
}

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [jobId, setJobId] = useState<number | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [results, setResults] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async () => {
    try {
      setError(null);
      setIsProcessing(true);
      setResults(null);
      
      // Basic URL validation
      try {
        new URL(videoUrl);
      } catch {
        throw new Error('Please enter a valid URL');
      }
      
      const response = await axios.post('/api/process', { video_url: videoUrl });
      setJobId(response.data.job_id);
      setStatus(response.data.status);
      // Start polling for status
      pollStatus(response.data.job_id);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || err.message || 'An error occurred');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
      setIsProcessing(false);
    }
  };

  const pollStatus = async (id: number) => {
    try {
      const response = await axios.get(`/api/status/${id}`);
      setStatus(response.data.status);

      if (response.data.status === 'completed') {
        // Fetch results
        const resultsResponse = await axios.get<ProcessingResult>(`/api/results/${id}`);
        setResults(resultsResponse.data);
        setIsProcessing(false);
      } else if (response.data.status === 'failed') {
        const errorResponse = await axios.get(`/api/error/${id}`);
        setError(errorResponse.data.error || 'Job processing failed');
        setIsProcessing(false);
      } else {
        // Continue polling
        setTimeout(() => pollStatus(id), 5000);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || err.message || 'An error occurred while checking status');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
      setIsProcessing(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setVideoUrl(e.target.value);
    setError(null);
  };

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'completed': return 'green';
      case 'failed': return 'red';
      case 'processing': return 'blue';
      default: return 'gray';
    }
  };

  return (
    <MantineProvider withGlobalStyles withNormalizeCSS>
      <Container size="md" py="xl">
        <Stack spacing="lg">
          <Title order={1}>Video Processing App</Title>
          
          <Paper shadow="xs" p="md">
            <Stack spacing="md">
              <TextInput
                label="Video URL"
                placeholder="Enter video URL (e.g., YouTube, direct MP4 link)"
                value={videoUrl}
                onChange={handleInputChange}
                error={error}
                disabled={isProcessing}
              />
              <Button 
                onClick={handleSubmit} 
                disabled={!videoUrl || isProcessing}
                loading={isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Process Video'}
              </Button>
            </Stack>
          </Paper>

          {error && (
            <Alert color="red" title="Error">
              {error}
            </Alert>
          )}

          {jobId && status && (
            <Paper shadow="xs" p="md">
              <Stack spacing="xs">
                <Text>Job ID: {jobId}</Text>
                <Text color={getStatusColor(status)}>Status: {status}</Text>
                {status === 'processing' && <Progress value={100} animate />}
              </Stack>
            </Paper>
          )}

          {results && (
            <Paper shadow="xs" p="md">
              <Stack spacing="md">
                <Title order={2}>Results</Title>
                
                <div>
                  <Title order={3}>Transcription</Title>
                  <Paper withBorder p="sm">
                    <Text>{results.transcription}</Text>
                  </Paper>
                </div>

                <div>
                  <Title order={3}>Action Points</Title>
                  {results.action_points.map((point, index) => (
                    <Paper key={index} withBorder p="md" mt="xs">
                      <Text weight={700} color={point.priority === 'High' ? 'red' : point.priority === 'Medium' ? 'orange' : 'blue'}>
                        Action: {point.action}
                      </Text>
                      {point.context && (
                        <Text size="sm" mt="xs" color="dimmed">
                          Context: {point.context}
                        </Text>
                      )}
                      <Text size="sm" mt="xs" weight={500} color={point.priority === 'High' ? 'red' : point.priority === 'Medium' ? 'orange' : 'blue'}>
                        Priority: {point.priority}
                      </Text>
                    </Paper>
                  ))}
                </div>
              </Stack>
            </Paper>
          )}
        </Stack>
      </Container>
    </MantineProvider>
  );
}

export default App; 