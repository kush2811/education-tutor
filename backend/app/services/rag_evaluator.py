"""Automated evaluation and benchmarking suite for Educational RAG performance, relevance, and citations."""

import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.rag import (
    RAGQueryRequest,
    RAGEvaluationReport,
    RAGEvaluationSampleResult,
)
from app.services.rag_service import rag_service

# Benchmark evaluation dataset with positive STEM curriculum inquiries and out-of-corpus negative probes
BENCHMARK_EVAL_DATASET = [
    {
        "id": "eval_01_physics",
        "question": "What is Newton's second law of motion and how is force calculated?",
        "subject": "Physics",
        "expected_sources": ["ncert-physics-class11", "openstax-physics-vol1"],
        "expected_keywords": ["force", "mass", "acceleration", "f = ma"],
        "should_find_context": True
    },
    {
        "id": "eval_02_math",
        "question": "State the standard form of a quadratic equation and the quadratic formula.",
        "subject": "Mathematics",
        "expected_sources": ["ncert-math-class10"],
        "expected_keywords": ["quadratic", "roots", "discriminant", "ax^2"],
        "should_find_context": True
    },
    {
        "id": "eval_03_chemistry",
        "question": "Explain the difference between covalent and ionic chemical bonds.",
        "subject": "Chemistry",
        "expected_sources": ["ncert-chemistry-class12", "libretexts-chem"],
        "expected_keywords": ["covalent", "ionic", "electron", "sharing"],
        "should_find_context": True
    },
    {
        "id": "eval_04_cs",
        "question": "What is binary search algorithm and its time complexity in sorted arrays?",
        "subject": "Computer Science",
        "expected_sources": ["nptel-cs-foundations", "mit-ocw-6-0001", "python-docs-312"],
        "expected_keywords": ["binary search", "sorted", "divide", "logarithmic", "o(log n)"],
        "should_find_context": True
    },
    {
        "id": "eval_05_trig",
        "question": "What is the Pythagorean trigonometric identity relating sine and cosine?",
        "subject": "Mathematics",
        "expected_sources": ["ncert-math-class10"],
        "expected_keywords": ["sin", "cos", "identity", "1"],
        "should_find_context": True
    },
    {
        "id": "eval_06_out_of_corpus",
        "question": "Who was the emperor during the Council of Nicaea in 325 AD and what were the tax reforms?",
        "subject": "History",
        "expected_sources": [],
        "expected_keywords": [],
        "should_find_context": False  # Must test uncertainty communication when data is missing!
    }
]


class EducationalRAGEvaluator:
    """Runs automated benchmark tests and measures retrieval precision, recall@K, citation accuracy, and latency."""

    def run_benchmark(self, db: Session) -> RAGEvaluationReport:
        """Execute evaluation across the benchmark dataset and compile quality metrics."""
        results: List[RAGEvaluationSampleResult] = []

        total_relevance = 0.0
        total_recall = 0.0
        total_latency = 0.0
        correct_uncertainty_count = 0
        valid_citations_count = 0
        total_citations_evaluated = 0

        for sample in BENCHMARK_EVAL_DATASET:
            t0 = time.perf_counter()
            req = RAGQueryRequest(
                query=sample["question"],
                subject=sample["subject"] if sample["subject"] != "History" else None,
                top_k=5,
                enable_hybrid=True,
                enable_reranking=True,
                confidence_threshold=0.25
            )
            rag_res = rag_service.execute_rag(req, db=db)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            total_latency += latency_ms

            retrieved_source_ids = [c.source_id for c in rag_res.citations]
            
            # Check Recall@K
            expected_sources = sample["expected_sources"]
            if expected_sources:
                hits = set(expected_sources).intersection(set(retrieved_source_ids))
                recall_val = len(hits) / float(len(expected_sources))
            else:
                # Negative sample: Recall is 1.0 if no sources were erroneously attached
                recall_val = 1.0 if not retrieved_source_ids else 0.0

            # Check Uncertainty Accuracy
            if not sample["should_find_context"]:
                # System should flag insufficient context and communicate uncertainty
                uncertainty_passed = (not rag_res.is_context_sufficient) or ("insufficient" in rag_res.answer.lower())
                if uncertainty_passed:
                    correct_uncertainty_count += 1
            else:
                uncertainty_passed = rag_res.is_context_sufficient
                if uncertainty_passed:
                    correct_uncertainty_count += 1

            # Check Citation Validity: Never generate fake citations
            for cit in rag_res.citations:
                total_citations_evaluated += 1
                if cit.source_id and cit.source_name and cit.source_url.startswith("http"):
                    valid_citations_count += 1

            sample_passed = (recall_val > 0.0 or not sample["should_find_context"]) and uncertainty_passed

            results.append(RAGEvaluationSampleResult(
                question_id=sample["id"],
                question=sample["question"],
                subject=sample["subject"],
                expected_sources=expected_sources,
                retrieved_sources=retrieved_source_ids,
                recall_at_k=round(recall_val, 3),
                relevance_score=round(1.0 if sample_passed else 0.5, 3),
                is_context_sufficient=rag_res.is_context_sufficient,
                expected_context_found=sample["should_find_context"],
                latency_ms=round(latency_ms, 2),
                sample_passed=sample_passed
            ))

            total_relevance += (1.0 if sample_passed else 0.5)
            total_recall += recall_val

        n = len(BENCHMARK_EVAL_DATASET)
        mean_relevance = total_relevance / float(n)
        mean_recall = total_recall / float(n)
        mean_lat = total_latency / float(n)
        uncertainty_acc = correct_uncertainty_count / float(n)
        citation_prec = (valid_citations_count / float(total_citations_evaluated)) if total_citations_evaluated > 0 else 1.0

        return RAGEvaluationReport(
            total_samples=n,
            mean_retrieval_relevance=round(mean_relevance, 3),
            mean_recall_at_k=round(mean_recall, 3),
            citation_precision=round(citation_prec, 3),
            uncertainty_accuracy=round(uncertainty_acc, 3),
            mean_latency_ms=round(mean_lat, 2),
            results=results
        )


rag_evaluator = EducationalRAGEvaluator()
