<?php

namespace App\Filament\Customer\Resources\Requests\Schemas;

use App\Models\Request;
use Filament\Actions\Action;
use Filament\Forms\Components\Checkbox;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Slider;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Textarea;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Illuminate\Support\Facades\Auth;

class RequestForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Входные данные')->schema([
//                    TextInput::make('user_id')
//                        ->required()
//                        ->default(Auth::id())
//                        ->hidden()
//                        ->numeric(),
//                    TextInput::make('status')
//                        ->required()
//                        ->hidden()
//                        ->default('created'),
                    TextInput::make('loan_amount')
                        ->label('Желаемая вами сумма кредита')
                        ->numeric()
                        ->inputMode('decimal')
                        ->prefix('₽')
                        ->placeholder('Например, 500 000')
                        ->required()
                        ->minValue(100_000)
                        ->maxValue(10_000_000)
                        ->step(100_000)
                        ->helperText('Введите сумму от 10 000 до 10 000 000 ₽'),
                    Select::make('borrower')
                        ->required()
                        ->label('Заёмщик')
                        ->preload()
                        ->createOptionForm([
                            TextInput::make('name')
                                ->label('Должность заёмщика')
                                ->required()
                                ->maxLength(255),
                        ])->options(Request::BORROWERS)
                        ->helperText('Выберите должность заёмщика или введите свой вариант')
                        ->default('ceo'),
                    Select::make('target')
                        ->required()
                        ->label('Цель кредитования')
                        ->options(Request::CREDIT_TARGETS)
                        ->helperText('Укажите цель кредитования')
                        ->default('Refinancing'),
//                    Textarea::make('credit_info')
//                        ->default(null)
//                        ->columnSpanFull(),
                    Checkbox::make('сonsent_processing_data_credit_history')
                        ->label('Согласие на обработку данных и кредитной истории')
                        ->required()
                        ->accepted()
                        ->dehydrated(),

                ]),
//                Section::make('')->schema([
//
//                ])
            ]);
    }
}
