<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Request extends Model
{
    public const  REQUEST_CREATED = 'created';
    public const REQUEST_IN_PROCESS = 'in_process';
    public const REQUEST_ACCEPTED = 'accepted';
    public const REQUEST_REJECTED = 'rejected';
    public const CONTRACT_SIGNED = 'signed';

    public const CREDIT_TARGETS = [
        'increasing_working_capital' => 'Пополнения оборотных средств',
        'acquisition_equipment. ' => 'Приобретение оборудования',
        'commercial_real_estate. ' => 'Коммерческая недвижимость',
        'Refinancing' => 'Рефинансирование',
    ];

    public const BORROWERS = [
        'ceo' => 'Гендиректор',
    ];

    public $fillable = [
        'user_id',
        'status',
        'credit_info',
        'admin_comment',
        'target',
        'borrower',
        'loan_amount'
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
